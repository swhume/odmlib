import unittest
import odmlib.odm_1_3_2.model as ODM


class TestAdminData(unittest.TestCase):
    def test_User(self):
        user = ODM.User(OID="ODM.U.3245", UserType="Sponsor")
        user.FirstName = ODM.FirstName(_content="John")
        user.LastName = ODM.LastName(_content="Rockerfeller")
        user.Organization = ODM.Organization(_content="Cleveland Clinic")
        user.Email.append(ODM.Email(_content="jrocker@clevelandclinic.org"))
        self.assertEqual(user.Email[0]._content, "jrocker@clevelandclinic.org")


if __name__ == '__main__':
    unittest.main()
