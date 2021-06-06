import unittest
import odmlib.odm_1_3_2.model as ODM
import datetime
import odmlib.odm_parser as ODM_PARSER
import xml.etree.ElementTree as ET
import odmlib.ns_registry as NS
import odmlib.odm_loader as OL
import odmlib.loader as LD

ODM_XML_FILE = "./data/simple_create.xml"
ODM_JSON_FILE = "./data/simple_create.json"


class MyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        current_datetime = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
        root = ODM.ODM(FileOID="ODM.DEMO.001", Granularity="Metadata", AsOfDateTime=current_datetime,
                       CreationDateTime=current_datetime, ODMVersion="1.3.2", FileType="Snapshot",
                       Originator="swhume", SourceSystem="odmlib", SourceSystemVersion="0.1")

        # create Study and add to ODM
        root.Study.append(ODM.Study(OID="ODM.GET.STARTED"))

        # create the global variables
        root.Study[0].GlobalVariables = ODM.GlobalVariables()
        root.Study[0].GlobalVariables.StudyName = ODM.StudyName(_content="Get Started with ODM XML")
        root.Study[0].GlobalVariables.StudyDescription = ODM.StudyDescription(
            _content="Demo to get started with odmlib")
        root.Study[0].GlobalVariables.ProtocolName = ODM.ProtocolName(_content="ODM XML Get Started")

        # create the MetaDataVersion
        root.Study[0].MetaDataVersion.append(ODM.MetaDataVersion(OID="MDV.DEMO-ODM-01", Name="Get Started MDV",
                                                                 Description="Get Started Demo"))
        # create Protocol
        p = ODM.Protocol()
        p.Description = ODM.Description()
        p.Description.TranslatedText.append(ODM.TranslatedText(_content="Get Started Protocol", lang="en"))
        p.StudyEventRef.append(ODM.StudyEventRef(StudyEventOID="BASELINE", OrderNumber=1, Mandatory="Yes"))
        root.Study[0].MetaDataVersion[0].Protocol = p

        # create a StudyEventDef
        sed = ODM.StudyEventDef(OID="BASELINE", Name="Baseline Visit", Repeating="No", Type="Scheduled")
        sed.FormRef.append(ODM.FormRef(FormOID="ODM.F.DM", Mandatory="Yes", OrderNumber=1))
        root.Study[0].MetaDataVersion[0].StudyEventDef.append(sed)

        # create a FormDef
        fd = ODM.FormDef(OID="ODM.F.DM", Name="Demographics", Repeating="No")
        fd.ItemGroupRef.append(ODM.ItemGroupRef(ItemGroupOID="ODM.IG.DM", Mandatory="Yes", OrderNumber=2))
        root.Study[0].MetaDataVersion[0].FormDef.append(fd)

        # create an ItemGroupDef
        igd = ODM.ItemGroupDef(OID="ODM.IG.DM", Name="Demographics", Repeating="No")
        igd.ItemRef.append(ODM.ItemRef(ItemOID="ODM.IT.DM.BRTHYR", Mandatory="Yes"))
        root.Study[0].MetaDataVersion[0].ItemGroupDef.append(igd)

        # create an ItemDef
        itd = ODM.ItemDef(OID="ODM.IT.DM.BRTHYR", Name="Birth Year", DataType="integer")
        itd.Description = ODM.Description()
        itd.Description.TranslatedText.append(ODM.TranslatedText(_content="Year of the subject's birth", lang="en"))
        itd.Question = ODM.Question()
        itd.Question.TranslatedText.append(ODM.TranslatedText(_content="Birth Year", lang="en"))
        itd.Alias.append(ODM.Alias(Context="CDASH", Name="BRTHYR"))
        itd.Alias.append(ODM.Alias(Context="SDTM", Name="BRTHDTC"))
        root.Study[0].MetaDataVersion[0].ItemDef.append(itd)

        # save the new ODM document to an ODM XML file
        root.write_xml(ODM_XML_FILE)

        # save the same ODM document to a JSON file
        root.write_json(ODM_JSON_FILE)


    def test_read_odm_xml(self):
        loader = LD.ODMLoader(OL.XMLODMLoader(model_package="odm_1_3_2", ns_uri="http://www.cdisc.org/ns/odm/v1.3"))
        loader.open_odm_document(ODM_XML_FILE)
        mdv = loader.MetaDataVersion()
        item_list = mdv.ItemDef
        item = item_list[0]
        self.assertEqual(item.OID, "ODM.IT.DM.BRTHYR")
        # tests the __len__ in ItemGroupDef
        self.assertEqual(len(item_list), 1)

    def test_read_odm_json(self):
        loader = LD.ODMLoader(OL.JSONODMLoader(model_package="odm_1_3_2"))
        loader.open_odm_document(ODM_JSON_FILE)
        mdv = loader.MetaDataVersion()
        igd_list = mdv.ItemGroupDef
        igd = igd_list[0]
        self.assertEqual(igd.OID, "ODM.IG.DM")
        # tests the __len__ in ItemGroupDef
        self.assertEqual(len(igd_list), 1)
