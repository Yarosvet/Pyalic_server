from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from ..db import models
from . import status
from .sessions import search_sessions, create_session


async def process_check_request(license_key: str, fingerprint: str, session: AsyncSession) -> tuple[bool, str]:
    # Get signature
    r = await session.execute(select(models.Signature).filter_by(license_key=license_key).options(
        selectinload(models.Signature.product), selectinload(models.Signature.installations)))
    sig = r.scalar_one_or_none()
    if sig is None:
        return False, status.INVALID_KEY
    # Check license period
    current_period = datetime.utcnow() - sig.activation_date if sig.activation_date is not None else timedelta(
        seconds=0)
    if sig.product.sig_period is not None and sig.product.sig_period < current_period:
        return False, status.LICENSE_EXPIRED
    # Check installation limit
    current_inst = None
    if sig.product.sig_install_limit is not None:
        r = await session.execute(select(models.Installation).filter_by(signature_id=sig.id, fingerprint=fingerprint))
        current_inst = r.scalar_one_or_none()
        if current_inst is None and len(sig.installations) >= sig.product.sig_install_limit:
            return False, status.INSTALLATIONS_LIMIT
    # Check sessions limit
    if sig.product.sig_sessions_limit is not None and \
            len(await search_sessions(sig.id)) >= sig.product.sig_sessions_limit:
        return False, status.SESSIONS_LIMIT
    # If all Ok, activate Signature if needed
    if sig.activation_date is None:
        sig.activation_date = datetime.utcnow()
    # And register installation if it's a new one
    if current_inst is None:
        current_inst = models.Installation(signature_id=sig.id, fingerprint=fingerprint)
        session.add(current_inst)
        await session.commit()
    # Start a new session for this signature
    sig_ends = (sig.product.sig_period + sig.activation_date).timestamp() if sig.product.sig_period is not None else 0
    session_id = await create_session(sig.id, signature_ends=int(sig_ends))
    return True, session_id
