from unittest import TestCase
import odmlib.define_2_0.model as DEFINE
import xml.etree.ElementTree as ET


class TestValueListDef(TestCase):
    def test_value_list_def(self):
        vld = DEFINE.ValueListDef(OID="VL.DA.DAORRES")
        vld.ItemRef.append(DEFINE.ItemRef(ItemOID="IT.DA.DAORRES.DISPAMT", OrderNumber="1", Mandatory="Yes"))
        vld.ItemRef[0].WhereClauseRef.append(DEFINE.WhereClauseRef(WhereClauseOID="WC.DA.DATESTCD.DISPAMT"))
        vld.ItemRef.append(DEFINE.ItemRef(ItemOID="IT.DA.DAORRES.RETAMT", OrderNumber="2", Mandatory="No"))
        vld.ItemRef[1].WhereClauseRef.append(DEFINE.WhereClauseRef(WhereClauseOID="WC.DA.DATESTCD.RETAMT"))
        self.assertEqual("WC.DA.DATESTCD.RETAMT", vld.ItemRef[1].WhereClauseRef[0].WhereClauseOID)
        vld_dict = vld.to_dict()
        print(vld_dict)
        expected_dict = {'OID': 'VL.DA.DAORRES', 'ItemRef':
            [{'ItemOID': 'IT.DA.DAORRES.DISPAMT', 'OrderNumber': 1, 'Mandatory': 'Yes', 'WhereClauseRef':
                [{'WhereClauseOID': 'WC.DA.DATESTCD.DISPAMT'}]},
             {'ItemOID': 'IT.DA.DAORRES.RETAMT', 'OrderNumber': 2, 'Mandatory': 'No', 'WhereClauseRef':
                 [{'WhereClauseOID': 'WC.DA.DATESTCD.RETAMT'}]}]}
        self.assertDictEqual(vld_dict, expected_dict)

    def test_where_clause_def(self):
        wcd = DEFINE.WhereClauseDef(OID="WC.DA.DATESTCD.DISPAMT")
        wcd.RangeCheck.append(DEFINE.RangeCheck(SoftHard="Soft", ItemOID="IT.DA.DATESTCD", Comparator="EQ"))
        wcd.RangeCheck[0].CheckValue.append(DEFINE.CheckValue(_content="DISPAMT"))
        self.assertEqual("IT.DA.DATESTCD", wcd.RangeCheck[0].ItemOID)
        wcd_xml = wcd.to_xml()
        print(ET.tostring(wcd_xml, encoding='utf8', method='xml'))
        self.assertDictEqual({"OID": "WC.DA.DATESTCD.DISPAMT"}, wcd_xml.attrib)

    def test_leaf(self):
        leaf = DEFINE.leaf(ID="LF.blankcrf", href="blankcrf.pdf")
        leaf.title = DEFINE.title(_content="Annotated Case Report Form")
        self.assertEqual("LF.blankcrf", leaf.ID)
        leaf_dict = leaf.to_dict()
        print(leaf_dict)
        expected_dict = {'ID': 'LF.blankcrf', 'href': 'blankcrf.pdf', 'title':
            {'_content': 'Annotated Case Report Form'}}
        self.assertDictEqual(leaf_dict, expected_dict)

    def test_comment_def(self):
        comment = DEFINE.CommentDef(OID="COM.VS.VISITNUM")
        comment.Description.TranslatedText.append(DEFINE.TranslatedText(_content="Assigned from the TV domain based on the VISIT", lang="en"))
        self.assertEqual("COM.VS.VISITNUM", comment.OID)
