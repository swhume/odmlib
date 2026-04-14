"""OID lookup index for odmlib object trees.

Provides :class:`OIDIndex`, a fast lookup structure that maps OID values to
the odmlib objects that own them.  Build the index by calling
:meth:`~odmlib.odm_element.ODMElement.build_oid_index` on the root element,
then use :meth:`OIDIndex.find_all` to retrieve any element(s) by OID.

Example::

    idx = odm.build_oid_index()
    items = idx.find_all("IT.AGE")   # returns list of odmlib objects with OID "IT.AGE"
"""
from odmlib.exceptions import OdmlibOIDError


class OIDIndex:
    """A lookup index mapping OID values to odmlib element objects.

    Built by :meth:`~odmlib.odm_element.ODMElement.build_oid_index`.
    Multiple elements can share an OID value (the index stores all of them),
    but OID uniqueness is enforced separately by the OID checkers in
    :mod:`odmlib.oid_generator`.

    Attributes:
        oid_index (dict): Mapping of OID string → list of odmlib element objects.
    """

    def __init__(self):
        self.oid_index = {}

    def add_oid(self, oid, element):
        """Add an OID-to-element mapping to the index.

        Multiple elements with the same OID are appended to the same list
        (uniqueness is not enforced here; use the OID checkers for that).

        Args:
            oid (str): The OID value to index.
            element: The odmlib element object that owns this OID.
        """
        if oid not in self.oid_index:
            self.oid_index[oid] = []
        self.oid_index[oid].append(element)

    def find_all(self, oid):
        """Return all odmlib element objects with the given OID.

        Args:
            oid (str): The OID value to look up.

        Returns:
            list: All odmlib element objects registered under ``oid``.

        Raises:
            OdmlibOIDError: If the index is empty (not yet built) or if
                ``oid`` is not found in the index.
        """
        if not self.oid_index:
            raise OdmlibOIDError(
                f"The OID index is empty. Build the index prior to using find_all. OID {oid} not found.",
                attribute="OID",
                hint="Call build_oid_index() on the root ODM element before using find_all()",
            )
        elif oid not in self.oid_index:
            raise OdmlibOIDError(
                f"OID {oid} not found in the OID index.",
                attribute="OID",
                hint=f"Verify that an element with OID '{oid}' has been added to the model",
            )
        return self.oid_index[oid]
