from ..db import models

DEFAULT_PERMISSIONS = "manage_own_products,manage_own_users"
SUPERUSER = "superuser"


class InvalidPermissionsString(Exception):
    pass


ALL_PERMISSIONS = ['superuser', 'manage_own_products', 'manage_other_products', 'read_other_products',
                   'create_users', 'manage_own_users', 'manage_other_users']


class Permissions:
    def __init__(self, s: str):
        """
        User's permissions class
        :param s: Permissions string
        """
        self._validate(s)
        self._permissions = [el.strip() for el in s.split(',') if el.strip()]

    @staticmethod
    def _validate(s: str):
        for el in s.split(','):
            if el and el not in ALL_PERMISSIONS:
                raise InvalidPermissionsString(el)

    def __str__(self) -> str:
        return ','.join(self._permissions)

    def __iter__(self):
        return iter(self._permissions)

    def __contains__(self, item):
        return self._permissions.__contains__(item)

    def is_superuser(self) -> bool:
        return 'superuser' in self._permissions

    def can_manage_own_products(self) -> bool:
        return 'manage_own_products' in self._permissions or self.can_read_other_products() or self.is_superuser()

    def can_manage_other_products(self) -> bool:
        return 'manage_other_products' in self._permissions or self.is_superuser()

    def can_read_other_products(self) -> bool:
        return 'read_other_products' in self._permissions or self.can_manage_other_products() or self.is_superuser()

    def can_create_users(self) -> bool:
        return 'create_users' in self._permissions or self.is_superuser()

    def can_manage_own_users(self) -> bool:
        return 'manage_own_users' in self._permissions or self.can_create_users() or self.can_manage_other_users() \
            or self.is_superuser()

    def can_manage_other_users(self) -> bool:
        return 'manage_other_users' in self._permissions or self.is_superuser()


class VerifiablePermissions(Permissions):
    def __init__(self, u: 'models.User'):
        super().__init__(u.permissions)
        self._u = u

    def able_get_product(self, p: 'models.Product') -> bool:
        return (self.can_manage_own_products() and p in self._u.owned_products) or \
            (self.can_read_other_products() and p not in self._u.owned_products)

    def able_edit_product(self, p: 'models.Product') -> bool:
        return (self.can_manage_own_products() and p in self._u.owned_products) or \
            (self.can_manage_other_products() and p not in self._u.owned_products)

    def able_delete_product(self, p: 'models.Product') -> bool:
        return (self.can_manage_own_products() and p in self._u.owned_products) or \
            (self.can_manage_other_products() and p not in self._u.owned_products)

    def able_add_product(self) -> bool:
        return self.can_manage_own_products()

    def able_add_user(self, permissions: str) -> bool:
        try:
            perm_obj = Permissions(permissions)
        except InvalidPermissionsString:
            return False
        for p in perm_obj:
            if p not in self._u.get_permissions() and not self.is_superuser():
                return False
        return self.can_create_users()

    def able_edit_user(self, u: 'models.User', permissions: str | None = None) -> bool:
        if permissions is not None:
            try:
                perm_obj = Permissions(permissions)
            except InvalidPermissionsString:
                return False
            for p in perm_obj:
                if p not in self._u.get_permissions() and not self.is_superuser():
                    return False
        if u.master != self._u:
            return self.can_manage_other_users()
        return self.can_manage_own_users()

    def able_delete_user(self, u: 'models.User') -> bool:
        if u == self._u:
            return False
        if u.master != self._u:
            return self.can_manage_other_users()
        return self.can_manage_own_users()
