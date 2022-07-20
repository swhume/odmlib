

from re import S
from unittest import TestCase



class TestOIDRefODM(TestCase):

    def test_default_skipelem(self):
        from odmlib.odm_1_3_2.rules.oid_ref import OIDRef
        oidref = OIDRef()
        self.assertEqual(oidref.skip_elem, ["ODM"])
    
    
    def test_default_skipelem_plus(self):
        from odmlib.odm_1_3_2.rules.oid_ref import OIDRef
        oidref = OIDRef(skip_elems=["MetaDataVersion"])
        self.assertEqual(sorted(oidref.skip_elem), sorted(["ODM", "MetaDataVersion"]))

    def test_default_skipattr(self):
        from odmlib.odm_1_3_2.rules.oid_ref import OIDRef
        oidref = OIDRef()
        self.assertEqual(oidref.skip_attr, ["FileOID", "PriorFileOID"])
    
    
    def test_default_skipattr_plus(self):
        from odmlib.odm_1_3_2.rules.oid_ref import OIDRef
        oidref = OIDRef(skip_attrs=["LastUpdated"])
        self.assertEqual(sorted(oidref.skip_attr), sorted(["LastUpdated", "FileOID", "PriorFileOID"]))
    

class TestOIDRefDefine2(TestCase):

    DEFAULT_ATTRS = [
            "FileOID",
            "PriorFileOID",
            "StudyOID",
            "MetaDataVersionOID",
            "ItemGroupOID",
        ]
    DEFAULT_ELEMS = [
            "ODM",
            "Study",
            "MetaDataVersion",
            "ItemGroupDef",
        ] 
    def test_default_skipelem(self):
        from odmlib.define_2_0.rules.oid_ref import OIDRef
        oidref = OIDRef()
        self.assertEqual(oidref.skip_elem, self.DEFAULT_ELEMS)
    
    
    def test_default_skipelem_plus(self):
        from odmlib.define_2_0.rules.oid_ref import OIDRef
        oidref = OIDRef(skip_elems=["ItemRef"])
        self.assertEqual(sorted(oidref.skip_elem), sorted(self.DEFAULT_ELEMS + ["ItemRef"]))
    
    def test_default_skipattr(self):
        from odmlib.define_2_0.rules.oid_ref import OIDRef
        oidref = OIDRef()
        self.assertEqual(oidref.skip_attr, self.DEFAULT_ATTRS)
    
    def test_default_skipattr_plus(self):
        from odmlib.define_2_0.rules.oid_ref import OIDRef
        oidref = OIDRef(skip_attrs=["LastUpdated"])
        self.assertEqual(sorted(oidref.skip_attr), sorted(self.DEFAULT_ATTRS + ["LastUpdated"]))
    
class TestOIDRefDefine21(TestCase):

    DEFAULT_ATTRS = [
            "FileOID",
            "PriorFileOID",
            "StudyOID",
            "MetaDataVersionOID",
            "ItemGroupOID",
        ]
    DEFAULT_ELEMS = [
            "ODM",
            "Study",
            "MetaDataVersion",
            "ItemGroupDef",
        ] 
    def test_default_skipelem(self):
        from odmlib.define_2_1.rules.oid_ref import OIDRef
        oidref = OIDRef()
        self.assertEqual(oidref.skip_elem, self.DEFAULT_ELEMS)
    
    
    def test_default_skipelem_plus(self):
        from odmlib.define_2_1.rules.oid_ref import OIDRef
        oidref = OIDRef(skip_elems=["ItemRef"])
        self.assertEqual(sorted(oidref.skip_elem), sorted(self.DEFAULT_ELEMS + ["ItemRef"]))
    
    def test_default_skipattr(self):
        from odmlib.define_2_1.rules.oid_ref import OIDRef
        oidref = OIDRef()
        self.assertEqual(oidref.skip_attr, self.DEFAULT_ATTRS)
    
    def test_default_skipattr_plus(self):
        from odmlib.define_2_1.rules.oid_ref import OIDRef
        oidref = OIDRef(skip_attrs=["LastUpdated"])
        self.assertEqual(sorted(oidref.skip_attr), sorted(self.DEFAULT_ATTRS + ["LastUpdated"]))
    
