"""
Test suite for the productdb.models module
"""
import pytest
import os
import tempfile
import datetime as _datetime
from hashlib import sha512
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files import File
from django.db.models import QuerySet
from mixer.backend.django import mixer
from app.productdb.models import Vendor, ProductList, JobFile, Product, UserProfile, ProductGroup, ProductMigrationSource, \
    ProductMigrationOption, ProductCheck, ProductCheckEntry, ProductCheckInputChunks, ProductIdNormalizationRule

pytestmark = pytest.mark.django_db


class TestJobFile:
    """Test JobFile model"""
    def test_auto_delete_job_file(self):
        # create temp test file
        filename = tempfile.mkstemp()[1]
        f = open(filename, 'w')
        f.write("These are the file contents")
        f.close()
        f = open(filename, "r")

        jf = JobFile.objects.create()
        jf.file.save("test file.txt", File(f))

        assert JobFile.objects.count() == 1, "A single object should exist in the database"
        assert os.path.exists(jf.file.path), "file should be created in the data directory"

        JobFile.objects.all().first().delete()

        assert JobFile.objects.count() == 0, "Object should be deleted from the database"
        assert not os.path.exists(jf.file.path), "file should be remove automatically"


class TestVendorModel:
    """Test Vendor model"""
    @pytest.mark.usefixtures("import_default_vendors")
    def test_vendor_object(self):
        mixer.blend("productdb.Vendor")
        assert Vendor.objects.count() == 4, "an additional vendor should be created"

        expected_vendor_name = "unassigned"
        v = Vendor.objects.get(name=expected_vendor_name)

        assert expected_vendor_name == str(v), "unexpected string representation of the Vendor object"

    def test_vendor_unique_name_constraint(self):
        test_name = "my vendor"
        mixer.blend("productdb.Vendor", name=test_name)

        with pytest.raises(ValidationError) as exinfo:
            Vendor.objects.create(name=test_name)

        assert exinfo.match("name': \['Vendor with this Name already exists.")

    @pytest.mark.usefixtures("import_default_vendors")
    def test_delete_vendor(self):
        assert Vendor.objects.count() == 3, "default vendors not loaded successfully"

        # delete the predefined "unassigned" vendor is not allowed/possible
        expected_vendor_name = "unassigned"
        v = Vendor.objects.get(name=expected_vendor_name)

        with pytest.raises(Exception) as exinfo:
            v.delete()

        assert exinfo.match("Operation not allowed")

        # delete any other vendor is possible (also the predefined objects)
        expected_vendor_name = "Cisco Systems"
        v = Vendor.objects.get(name=expected_vendor_name)

        v.delete()

        assert Vendor.objects.count() == 2

    @pytest.mark.usefixtures("import_default_vendors")
    def test_default_vendor_fixture(self):
        # verify default vendors
        assert Vendor.objects.count() == 3, "three vendors should be part of the fixture"
        assert Vendor.objects.get(name="unassigned").pk == 0, "PK 0 should be unassigned"
        assert Vendor.objects.get(name="Cisco Systems").pk == 1, "PK 1 should be Cisco Systems"
        assert Vendor.objects.get(name="Juniper Networks").pk == 2, "PK 2 should be Juniper Networks"


class TestProductGroup:
    """Test ProductGroup model object"""
    @pytest.mark.usefixtures("import_default_vendors")
    def test_product_group(self):
        expected_product_group = "Test Product Group"
        v = Vendor.objects.get(id=1)
        pg = mixer.blend("productdb.ProductGroup", name=expected_product_group)
        p1 = mixer.blend("productdb.Product", vendor=v)
        p2 = mixer.blend("productdb.Product", vendor=v)
        assert str(pg) == expected_product_group, "unexpected string representation of the ProductGroup object"
        assert pg.get_all_products() is None, "If no Product is part of the group, it should return None"
        assert pg.vendor == Vendor.objects.get(id=0), "Should be associated to the unassigned vendor"

        # change vendor of group
        pg.vendor = v
        pg.save()

        # add products to group
        p1.product_group = pg
        p1.save()
        assert type(pg.get_all_products()) == QuerySet, "Should return a query set"
        assert pg.get_all_products().count() == 1, "should contain a single element"
        assert pg.get_all_products().first().product_id == p1.product_id, "should match the previous associated product"

        p2.product_group = pg
        p2.save()
        assert type(pg.get_all_products()) == QuerySet, "Should return a query set"
        assert pg.get_all_products().count() == 2, "should contain two elements"
        assert pg.get_all_products().filter(product_id=p2.product_id).count() == 1, \
            "the second product should be associated to the product group"

        # drop vendor from DB and verify SET_DEFAULT
        v.delete()
        pg = ProductGroup.objects.get(name=expected_product_group)
        assert pg.vendor is not None, "Should not use None value"
        assert pg.vendor.id == 0, "unassigned Vendor has the ID 0 by default"
        assert pg.vendor.name == "unassigned", "Unexpected vendor name"

    def test_product_group_and_vendor_unique_together_constraint(self):
        v1 = mixer.blend("productdb.Vendor", name="first vendor")
        v2 = mixer.blend("productdb.Vendor", name="second vendor")

        mixer.blend("productdb.ProductGroup", name="Group1", vendor=v1)
        mixer.blend("productdb.ProductGroup", name="Group2", vendor=v1)
        mixer.blend("productdb.ProductGroup", name="Group1", vendor=v2)

        assert ProductGroup.objects.count() == 3, "Three separate Product Groups should exist"

        # try to create another Group1 for the first vendor
        with pytest.raises(ValidationError) as exinfo:
            mixer.blend("productdb.ProductGroup", name="Group1", vendor=v1)

        assert exinfo.match("name': \['group name already defined for this vendor'")

    @pytest.mark.usefixtures("import_default_vendors")
    def test_product_group_vendor_change(self):
        v1 = Vendor.objects.get(name="unassigned")
        v2 = Vendor.objects.get(name="Cisco Systems")

        expected_product_group = "Test Product Group"
        pg = mixer.blend("productdb.ProductGroup", name=expected_product_group, vendor=v1)
        p1 = mixer.blend("productdb.Product", vendor=v2)
        p2 = mixer.blend("productdb.Product", vendor=v2)

        # change the vendor of a product group that has no products associated to it
        assert pg.get_all_products() is None, "No products are associated to the group and None should be returned"
        pg.vendor = v2
        pg.save()

        # add products to the group and try to change the vendor
        p1.product_group = pg
        p1.save()
        p2.product_group = pg
        p2.save()
        with pytest.raises(ValidationError) as exinfo:
            pg.vendor = v1
            pg.save()

        assert exinfo.match("cannot set new vendor as long as there are products associated to it")


@pytest.mark.usefixtures("import_default_vendors")
class TestProduct:
    """Test Product model object"""
    def test_product(self):
        p = mixer.blend("productdb.Product")

        assert str(p) == p.product_id, "unexpected string representation of the Product object"

    def test_current_lifecycle_states(self):
        p = Product.objects.create(product_id="Test")
        assert p.current_lifecycle_states is None, "Nothing is defined for the product, should be None"

        # the update timestamp indicated that the product lifecycle state was checked
        p.eox_update_time_stamp = _datetime.datetime.now()
        assert p.current_lifecycle_states == [Product.NO_EOL_ANNOUNCEMENT_STR], "No EoX announcement found at this point"

        # set the eox announcement state
        p.eol_ext_announcement_date = _datetime.date.today()
        expected_output = [Product.EOS_ANNOUNCED_STR]
        assert p.current_lifecycle_states == expected_output, "EoL announcement should be visible"

        # set the End of Sale date
        p.end_of_sale_date = _datetime.date.today() + _datetime.timedelta(days=1)
        expected_output = [Product.EOS_ANNOUNCED_STR]
        assert p.current_lifecycle_states == expected_output, \
            "Nothing should change, because the date is in the future"
        p.end_of_sale_date = _datetime.date.today()
        expected_output = [Product.END_OF_SALE_STR]
        assert p.current_lifecycle_states == expected_output

        # set the End of new Service Attachment Date
        p.end_of_new_service_attachment_date = _datetime.date.today() + _datetime.timedelta(days=1)
        assert p.current_lifecycle_states == expected_output, \
            "Nothing should change, because the date is in the future"
        p.end_of_new_service_attachment_date = _datetime.date.today()
        expected_output = [Product.END_OF_SALE_STR, Product.END_OF_NEW_SERVICE_ATTACHMENT_STR]
        assert p.current_lifecycle_states == expected_output

        # set the End of SW maintenance date
        p.end_of_sw_maintenance_date = _datetime.date.today() + _datetime.timedelta(days=1)
        assert p.current_lifecycle_states == expected_output, \
            "Nothing should change, because the date is in the future"
        p.end_of_sw_maintenance_date = _datetime.date.today()
        expected_output = [
            Product.END_OF_SALE_STR,
            Product.END_OF_NEW_SERVICE_ATTACHMENT_STR,
            Product.END_OF_SW_MAINTENANCE_RELEASES_STR
        ]
        assert p.current_lifecycle_states == expected_output

        # set the End of Routine Failure Analysis date
        p.end_of_routine_failure_analysis = _datetime.date.today() + _datetime.timedelta(days=1)
        assert p.current_lifecycle_states == expected_output, \
            "Nothing should change, because the date is in the future"
        p.end_of_routine_failure_analysis = _datetime.date.today()
        expected_output = [
            Product.END_OF_SALE_STR,
            Product.END_OF_NEW_SERVICE_ATTACHMENT_STR,
            Product.END_OF_SW_MAINTENANCE_RELEASES_STR,
            Product.END_OF_ROUTINE_FAILURE_ANALYSIS_STR
        ]
        assert p.current_lifecycle_states == expected_output

        # set the End of Service Contract Renewal date
        p.end_of_service_contract_renewal = _datetime.date.today() + _datetime.timedelta(days=1)
        assert p.current_lifecycle_states == expected_output, \
            "Nothing should change, because the date is in the future"
        p.end_of_service_contract_renewal = _datetime.date.today()
        expected_output = [
            Product.END_OF_SALE_STR,
            Product.END_OF_NEW_SERVICE_ATTACHMENT_STR,
            Product.END_OF_SW_MAINTENANCE_RELEASES_STR,
            Product.END_OF_ROUTINE_FAILURE_ANALYSIS_STR,
            Product.END_OF_SERVICE_CONTRACT_RENEWAL_STR
        ]
        assert p.current_lifecycle_states == expected_output

        # set the End of Vulnerability/Security Support date
        p.end_of_sec_vuln_supp_date = _datetime.date.today() + _datetime.timedelta(days=1)
        assert p.current_lifecycle_states == expected_output, \
            "Nothing should change, because the date is in the future"
        p.end_of_sec_vuln_supp_date = _datetime.date.today()
        expected_output = [
            Product.END_OF_SALE_STR,
            Product.END_OF_NEW_SERVICE_ATTACHMENT_STR,
            Product.END_OF_SW_MAINTENANCE_RELEASES_STR,
            Product.END_OF_ROUTINE_FAILURE_ANALYSIS_STR,
            Product.END_OF_SERVICE_CONTRACT_RENEWAL_STR,
            Product.END_OF_VUL_SUPPORT_STR
        ]
        assert p.current_lifecycle_states == expected_output

        # set the End of Support date
        p.end_of_support_date = _datetime.date.today() + _datetime.timedelta(days=1)
        assert p.current_lifecycle_states == expected_output, \
            "Nothing should change, because the date is in the future"
        p.end_of_support_date = _datetime.date.today()
        assert p.current_lifecycle_states == [Product.END_OF_SUPPORT_STR]

    def test_product_id_unique_constraint(self):
        test_name = "my product id"
        mixer.blend("productdb.Product", product_id=test_name)

        with pytest.raises(ValidationError) as exinfo:
            Product.objects.create(product_id=test_name)

        assert exinfo.match("product_id': \['Product with this Product id already exists.'"), \
            "product ID must be unique in the database"

    def test_product_vendor_change(self):
        v1 = Vendor.objects.get(name="unassigned")
        v2 = Vendor.objects.get(name="Cisco Systems")

        p = mixer.blend("productdb.Product", vendor=v1)
        pg = mixer.blend("productdb.ProductGroup", vendor=v2)

        # change vendor of a product that is not associated to a product group
        p.vendor = v2
        p.save()
        assert p.vendor == v2

        # add the product to a group and try to change the vendor
        p.product_group = pg
        p.save()

        with pytest.raises(ValidationError) as exinfo:
            p.vendor = v1
            p.save()

        expected_message = "product_group': \['Invalid product group, group and product must be associated to the " \
                           "same vendor"
        assert exinfo.match(expected_message)

    def test_list_price_values(self):
        valid_values = [
            1000,
            100.00,
            0,
            0.00,
            1.1,
            0.53,
            "3.00",
            "3.50",
            "5"
        ]

        invalid_values = [
            {
                "value": -4,
                "exp_error": "list_price': \['Ensure this value is greater than or equal to 0"
            },
            {
                "value": -54.123,
                "exp_error": "list_price': \['Ensure this value is greater than or equal to 0"
            },
            {
                "value": -23.00,
                "exp_error": "list_price': \['Ensure this value is greater than or equal to 0"
            },
            {
                "value": "One",
                "exp_error": "value must be a float"
            }
        ]

        p = mixer.blend("productdb.Product", list_price=None)
        assert p.list_price is None

        for val in valid_values:
            p.list_price = val
            p.save()

        for ival in invalid_values:
            p.list_price = ival["value"]
            print(p.list_price)
            with pytest.raises(ValidationError) as exinfo:
                p.save()
            assert exinfo.match(ival["exp_error"])

    def test_product_eol_url_with_whitespace(self):
        p = mixer.blend("productdb.Product")

        assert p.eol_reference_url is None

        p.eol_reference_url = "http://localhost/valid_url.html"
        p.save()

        p.refresh_from_db()
        assert p.eol_reference_url == "http://localhost/valid_url.html"

        p.eol_reference_url = "  http://localhost/valid_url_with_whitespace.html  "
        p.save()

        p.refresh_from_db()
        assert p.eol_reference_url == "http://localhost/valid_url_with_whitespace.html"

        p.eol_reference_url = "some random invalid url"

        with pytest.raises(ValidationError) as exinfo:
            p.save()

        assert exinfo.match("eol_reference_url': \['Enter a valid URL.")

    def test_timestamp_values(self, monkeypatch):
        date = _datetime.date.today()
        first_date = _datetime.date(year=1970, day=1, month=1)

        p = mixer.blend("productdb.Product", update_timestamp=first_date, lc_state_sync=True)

        assert p.update_timestamp == first_date, "Date is not overwritten by the save methode, because the state " \
                                                 "sync was changed"
        assert p.list_price_timestamp is None, "No timestamp because no list price was set"

        # change the lc_sync_state (update_timestamp should not change)
        p = Product.objects.get(id=p.id)
        p.lc_state_sync = False
        p.save()

        assert p.update_timestamp == first_date, "timestamp not changed, only lc flag updated"
        assert p.list_price_timestamp is None, "timestamp not changed, only lc flag updated"

        p = Product.objects.get(id=p.id)
        p.description = "Test"
        p.save()

        assert p.update_timestamp == date, "timestamp updated"
        assert p.list_price_timestamp is None

        p = Product.objects.get(id=p.id)
        p.list_price = 1000
        p.save()

        assert p.update_timestamp == date, "also updated"
        assert p.list_price_timestamp == date, "list price changed, datetime should be set"


class TestProductList:
    """Test ProductList model object"""
    @pytest.mark.usefixtures("import_default_users")
    @pytest.mark.usefixtures("import_default_vendors")
    def test_product_list_created_without_a_product(self):
        # Product List must contain a single when created
        with pytest.raises(ValidationError) as exinfo:
            ProductList.objects.create(
                name="example product list",
                update_user=User.objects.get(username="api")
            )

        expected_message = r"'string_product_list': \['This field cannot be blank.'\]"
        assert exinfo.match(expected_message), "Should contain the error message for the string_product_list"

        pl = ProductList()
        pl.name = "example product list"
        with pytest.raises(ValidationError) as exinfo:
            pl.save()

        assert exinfo.match(expected_message), "Should contain the error message for the string_product_list"

    @pytest.mark.usefixtures("import_default_users")
    @pytest.mark.usefixtures("import_default_vendors")
    def test_product_list_name_unique_constraint(self):
        test_name = "test product list"
        mixer.blend("productdb.Product", product_id="myprod1")
        mixer.blend("productdb.ProductList", name=test_name, string_product_list="myprod1")

        with pytest.raises(ValidationError) as exinfo:
            ProductList.objects.create(
                name=test_name,
                string_product_list="myprod1",
                update_user=User.objects.get(username="api")
            )

        assert exinfo.match("name': \['Product List with this Product List Name already exists.'")

    @pytest.mark.usefixtures("import_default_vendors")
    def test_product_list_created_with_a_product(self):
        mixer.blend("productdb.Product", product_id="myprod1")

        # Product List must contain an element when created
        mixer.blend("productdb.ProductList", name="example product list", string_product_list="myprod1")
        assert ProductList.objects.count() == 1, "a ProductList should be created"
        assert ProductList.objects.all().first().update_date is not None, "The update date should not be None"
        assert ProductList.objects.all().first().update_user is not None, "The update user should not be None"

    @pytest.mark.usefixtures("import_default_vendors")
    def test_product_list(self):
        mixer.blend("productdb.Product", product_id="myprod1")
        mixer.blend("productdb.Product", product_id="myprod2")
        mixer.blend("productdb.Product", product_id="myprod3")
        pl = mixer.blend("productdb.ProductList", name="Test Product List", string_product_list="myprod1")

        assert pl.update_user is not None, "Should contain the update user"
        assert pl.update_date is not None, "Should contain the update timestamp"
        assert str(pl) == pl.name, "Unexpected string representation of the Product List"

        expected_product_list = ["myprod1"]
        expected_product_list_string = "myprod1"

        assert type(pl.get_product_list_objects()) == QuerySet, "Should return a QuerySet"
        assert pl.get_product_list_objects().count() == 1, "A single product should be part of the product list"
        assert type(pl.get_string_product_list_as_list()) == list, "expecting a list"
        assert pl.get_string_product_list_as_list() == expected_product_list, \
            "Unexpected String representation of the Product List elements"
        assert pl.string_product_list == expected_product_list_string, \
            "String in DB should only contain a sorted list with line breaks"

        # associate multiple elements to the list using line-breaks
        expected_product_list += ["myprod2", "myprod3"]
        expected_product_list_string = "myprod1\nmyprod2\nmyprod3"
        pl.string_product_list = "\n".join(expected_product_list)
        pl.save()

        assert type(pl.get_product_list_objects()) == QuerySet, "Should return a QuerySet"
        assert pl.get_product_list_objects().count() == 3, "A single product should be part of the product list"
        assert type(pl.get_string_product_list_as_list()) == list, "expecting a list"
        assert pl.get_string_product_list_as_list() == expected_product_list, \
            "Unexpected String representation of the Product List elements"
        assert pl.string_product_list == expected_product_list_string, \
            "String in DB should only contain a sorted list with line breaks"

        # associate multiple elements to the list using semicolon
        pl.string_product_list = ";".join(expected_product_list)
        pl.save()

        assert type(pl.get_product_list_objects()) == QuerySet, "Should return a QuerySet"
        assert pl.get_product_list_objects().count() == 3, "A single product should be part of the product list"
        assert type(pl.get_string_product_list_as_list()) == list, "expecting a list"
        assert pl.get_string_product_list_as_list() == expected_product_list, \
            "Unexpected String representation of the Product List elements"
        assert pl.string_product_list == expected_product_list_string, \
            "String in DB should only contain a sorted list with line breaks"

    @pytest.mark.usefixtures("import_default_vendors")
    def test_hash_function(self):
        mixer.blend("productdb.Product", product_id="myprod1")
        mixer.blend("productdb.Product", product_id="myprod2")
        mixer.blend("productdb.Product", product_id="myprod3")
        pl = mixer.blend("productdb.ProductList", name="Test Product List", string_product_list="myprod1")
        assert pl.hash is not None
        hash = pl.hash

        # change the name of the product list (should modify the hash)
        pl.name = "My new Name"
        pl.save()

        assert hash != pl.hash
        hash = pl.hash

        # change the string product list (should modify the hash)
        pl.string_product_list = "myprod1;myprod2;myprod3"
        pl.save()

        assert hash != pl.hash
        hash = pl.hash

        # change description (should not change the hash)
        pl.description = "Some other value"
        pl.save()

        assert hash == pl.hash


class TestUserProfile:
    """Test UserProfile model object"""
    @pytest.mark.usefixtures("import_default_vendors")
    def test_create_new_user_profile_when_user_is_created(self):
        assert UserProfile.objects.count() == 0, "No user profile should be created at this time"

        u = User.objects.create(username="My test user")
        assert UserProfile.objects.count() == 1, "A User Profile object should be created automatically"
        assert u.profile is not None, "User Profile should be associated to the new user"
        assert str(u.profile) == "User Profile for My test user", "Unexpected string representation of the User Profile"
        assert u.profile.regex_search is False, "the advanced search operation should be disabled by default"
        assert u.profile.preferred_vendor == Vendor.objects.get(id=1), "Default vendor should be defined"

    @pytest.mark.usefixtures("import_default_vendors")
    def test_natural_key_serialization(self):
        u = User.objects.create(username="test_user")
        assert UserProfile.objects.count() == 1, "A User Profile object should be created automatically"
        up = UserProfile.objects.get_by_natural_key(u.username)
        assert up is not None
        assert up.natural_key() == "test_user"


class TestProductMigrationSource:
    def test_model(self):
        pmiggrp = ProductMigrationSource.objects.create(name="Test", description="description")

        assert str(pmiggrp) == "Test"
        assert pmiggrp.preference == 50, "Default value"

        # test ordering
        pmiggrp2 = ProductMigrationSource.objects.create(
            name="Test2", preference=70
        )

        assert ProductMigrationSource.objects.count() == 2
        assert ProductMigrationSource.objects.all().first().name == pmiggrp2.name

        # test second
        ProductMigrationSource.objects.create(
            name="Test3", preference=70
        )

        assert ProductMigrationSource.objects.count() == 3
        assert ProductMigrationSource.objects.all().first().name == pmiggrp2.name

    def test_unique_name(self):
        test_name = "Test Migration Source"
        mixer.blend("productdb.ProductMigrationSource", name=test_name)

        with pytest.raises(ValidationError) as exinfo:
            ProductMigrationSource.objects.create(name=test_name)

        assert exinfo.match("\'name\': \[\'Product Migration Source with this Name already exists.\'\]")


@pytest.mark.usefixtures("import_default_vendors")
class TestProductCheck:
    """Test the ProductCheck and ProductCheckEntry model"""
    def test_model(self):
        test_product_string = "myprod"
        mixer.blend(
            "productdb.Product",
            product_id=test_product_string,
            vendor=Vendor.objects.get(id=1)
        )

        pc = ProductCheck.objects.create(name="Test", input_product_ids="TestTest")

        assert pc.migration_source is None
        assert pc.use_preferred_migration_source is True  # should be true, because no migration source is defined
        assert pc.input_product_ids_list == ["TestTest"]
        assert pc.last_change is not None
        assert pc.create_user is None
        assert pc.task_id is None   # used within the job scheduler
        assert pc.is_public is True  # no user defined, Product Check is public
        assert pc.in_progress is False  # no job
        assert str(pc) == "Test"

        # test list values
        pc.input_product_ids = "TestTest;Test;Test\nasdf"
        pc.save()

        assert pc.input_product_ids_list == ["Test", "Test", "TestTest", "asdf"]

        # test migration source
        pc.migration_source = mixer.blend("productdb.ProductMigrationSource", name="Test")
        pc.save()

        assert pc.use_preferred_migration_source is False

        # test create user
        pc.create_user = mixer.blend("auth.User")
        pc.save()

        assert pc.is_public is False

        # test in progress if task ID is set
        pc.task_id = "1234"
        pc.save()

        assert pc.in_progress is True

    def test_flexible_input_field(self):
        first_large_string = "".join(["\n" if e % 32 == 0 else "1" for e in range(1, 65536)])
        second_large_string = "".join(["\n" if e % 32 == 0 else "2" for e in range(1, 65536)])

        pc = ProductCheck.objects.create(name="Test", input_product_ids=first_large_string)

        # single chunk (maximum size)
        assert pc.productcheckinputchunks_set.count() == 1
        assert pc.input_product_ids == first_large_string

        # test setter property
        pc.input_product_ids = second_large_string

        sls_hash = sha512(second_large_string.encode()).digest()

        assert sha512(pc._input_product_ids.encode()).digest() == sls_hash, "internal buffer should be set"
        assert sha512(pc.input_product_ids.encode()).digest() == sls_hash, "Should return the buffer value"

        # save value
        pc.save()

        assert pc.productcheckinputchunks_set.count() == 1

        # read from DB
        read_pc = ProductCheck.objects.get(id=pc.id)

        assert sha512(read_pc.input_product_ids.encode()).digest() == sls_hash

        # test with multiple chunks
        very_large_string = first_large_string + second_large_string + first_large_string
        vls_hash = sha512(very_large_string.encode()).digest()

        # test setter property with very large string
        new_pc = ProductCheck.objects.create(name="Test", input_product_ids=very_large_string)

        assert sha512(new_pc._input_product_ids.encode()).digest() == vls_hash, "internal buffer should be set"
        assert sha512(new_pc.input_product_ids.encode()).digest() == vls_hash, "Should return the buffer value"

        # save value
        new_pc.save()

        assert new_pc.productcheckinputchunks_set.count() == 3
        assert ProductCheckInputChunks.objects.count() == 3 + 1

        # read and save again
        new_pc = ProductCheck.objects.get(id=new_pc.id)
        new_pc.save()

        assert sha512(new_pc.input_product_ids.encode()).digest() == vls_hash

    def test_basic_product_check(self):
        test_product_string = "myprod"
        test_list = "myprod;myprod\nmyprod;myprod\n" \
                    "Test;Test"
        p = mixer.blend(
            "productdb.Product",
            product_id=test_product_string,
            vendor=Vendor.objects.get(id=1)
        )
        pms1 = mixer.blend("productdb.ProductMigrationSource", name="Preferred Migration Source", preference=60)
        pms2 = mixer.blend("productdb.ProductMigrationSource", name="Another Migration Source")
        pmo1 = mixer.blend("productdb.ProductMigrationOption", product=p, migration_source=pms1,
                           replacement_product_id="replacement")
        pmo2 = mixer.blend("productdb.ProductMigrationOption", product=p, migration_source=pms2,
                           replacement_product_id="other_replacement")
        pl = mixer.blend(
            "productdb.ProductList",
            name="TestList",
            string_product_list="myprod"
        )
        pl2 = mixer.blend(
            "productdb.ProductList",
            name="AnotherTestList",
            string_product_list="myprod"
        )

        pc = ProductCheck.objects.create(name="Test", input_product_ids=test_list)
        pc.perform_product_check()
        assert pc.productcheckentry_set.count() == 2

        in_db = pc.productcheckentry_set.get(input_product_id="myprod")
        assert in_db.amount == 4
        assert in_db.in_database is True
        assert in_db.product_in_database is not None
        assert in_db.part_of_product_list == pl2.hash + "\n" + pl.hash
        assert in_db.migration_product.replacement_product_id == pmo1.replacement_product_id
        assert str(in_db) == "Test: myprod (4)"

        pl_names = in_db.get_product_list_names()
        assert len(pl_names) == 2
        assert "AnotherTestList" in pl_names
        assert "TestList" in pl_names

        not_in_db = pc.productcheckentry_set.get(input_product_id="Test")
        assert not_in_db.amount == 2
        assert not_in_db.in_database is False
        assert not_in_db.product_in_database is None
        assert not_in_db.part_of_product_list == ""
        assert not_in_db.migration_product is None

        # change product list (the name should not appear anymore in the product check)
        pl.name = "RenamedTestList"
        pl.save()

        pl_names = in_db.get_product_list_names()
        assert len(pl_names) == 1
        assert "AnotherTestList" in pl_names

        # run again (should reset and recreate the results)
        pc.perform_product_check()
        assert pc.productcheckentry_set.count() == 2
        assert ProductCheckEntry.objects.all().count() == 2

        # run again with a specific migration source
        pc.migration_source = pms2  # use the less preferred migration source

        pc.perform_product_check()
        assert pc.productcheckentry_set.count() == 2

        in_db = pc.productcheckentry_set.get(input_product_id="myprod")
        assert in_db.amount == 4
        assert in_db.in_database is True
        assert in_db.product_in_database is not None
        assert in_db.part_of_product_list == pl2.hash + "\n" + pl.hash
        assert in_db.migration_product.replacement_product_id == pmo2.replacement_product_id

        pl_names = in_db.get_product_list_names()
        assert len(pl_names) == 2
        assert "AnotherTestList" in pl_names
        assert "RenamedTestList" in pl_names  # back after product check runs again

        not_in_db = pc.productcheckentry_set.get(input_product_id="Test")
        assert not_in_db.amount == 2
        assert not_in_db.in_database is False
        assert not_in_db.product_in_database is None
        assert not_in_db.part_of_product_list == ""
        assert not_in_db.migration_product is None

    def test_recursive_product_check(self):
        test_product_string = "myprod"
        test_list = "myprod;myprod\nmyprod;myprod\n" \
                    "Test;Test"
        p = mixer.blend(
            "productdb.Product",
            product_id=test_product_string,
            vendor=Vendor.objects.get(id=1),
            eox_update_time_stamp=_datetime.datetime.utcnow(),
            eol_ext_announcement_date=_datetime.date(2016, 1, 1),
            end_of_sale_date=_datetime.date(2016, 1, 1)
        )
        p2 = mixer.blend(
            "productdb.Product",
            product_id="replacement_pid",
            vendor=Vendor.objects.get(id=1),
            eox_update_time_stamp=_datetime.datetime.utcnow(),
            eol_ext_announcement_date=_datetime.date(2016, 1, 1),
            end_of_sale_date=_datetime.date(2016, 1, 1)
        )
        mixer.blend(
            "productdb.Product",
            product_id="another_replacement_pid",
            vendor=Vendor.objects.get(id=1)
        )
        pms = mixer.blend("productdb.ProductMigrationSource", name="Preferred Migration Source", preference=60)
        mixer.blend("productdb.ProductMigrationOption", product=p, migration_source=pms,
                    replacement_product_id="replacement_pid")
        mixer.blend("productdb.ProductMigrationOption", product=p2, migration_source=pms,
                    replacement_product_id="another_replacement_pid")
        pl = mixer.blend(
            "productdb.ProductList",
            name="TestList",
            string_product_list="myprod"
        )
        pl2 = mixer.blend(
            "productdb.ProductList",
            name="AnotherTestList",
            string_product_list="myprod"
        )

        pc = ProductCheck.objects.create(name="Test", input_product_ids=test_list, migration_source=pms)
        pc.perform_product_check()
        assert pc.productcheckentry_set.count() == 2

        in_db = pc.productcheckentry_set.get(input_product_id="myprod")
        assert in_db.amount == 4
        assert in_db.in_database is True
        assert in_db.product_in_database is not None
        assert in_db.part_of_product_list == pl2.hash + "\n" + pl.hash
        assert in_db.migration_product.replacement_product_id == "another_replacement_pid"  # use the last element in the path

        pl_names = in_db.get_product_list_names()
        assert len(pl_names) == 2
        assert "AnotherTestList" in pl_names
        assert "TestList" in pl_names

        not_in_db = pc.productcheckentry_set.get(input_product_id="Test")
        assert not_in_db.amount == 2
        assert not_in_db.in_database is False
        assert not_in_db.product_in_database is None
        assert not_in_db.part_of_product_list == ""
        assert not_in_db.migration_product is None

    def test_basic_product_check_with_less_preferred_migration_source(self):
        """only Product Migration sources that have a preference > 25 should be considered as preferred"""
        test_product_string = "myprod"
        test_list = "myprod;myprod\nmyprod;myprod\n" \
                    "Test;Test"
        p = mixer.blend(
            "productdb.Product",
            product_id=test_product_string,
            vendor=Vendor.objects.get(id=1)
        )
        pms1 = mixer.blend("productdb.ProductMigrationSource", name="Preferred Migration Source", preference=25)
        pms2 = mixer.blend("productdb.ProductMigrationSource", name="Another Migration Source", preference=10)
        pmo1 = mixer.blend("productdb.ProductMigrationOption", product=p, migration_source=pms1,
                           replacement_product_id="replacement")
        pmo2 = mixer.blend("productdb.ProductMigrationOption", product=p, migration_source=pms2,
                           replacement_product_id="other_replacement")
        pl = mixer.blend(
            "productdb.ProductList",
            name="TestList",
            string_product_list="myprod"
        )
        pl2 = mixer.blend(
            "productdb.ProductList",
            name="AnotherTestList",
            string_product_list="myprod"
        )

        pc = ProductCheck.objects.create(name="Test", input_product_ids=test_list)
        pc.perform_product_check()
        assert pc.productcheckentry_set.count() == 2

        in_db = pc.productcheckentry_set.get(input_product_id="myprod")
        assert in_db.amount == 4
        assert in_db.migration_product is None
        assert str(in_db) == "Test: myprod (4)"

        pl_names = in_db.get_product_list_names()
        assert len(pl_names) == 2
        assert "AnotherTestList" in pl_names
        assert "TestList" in pl_names

        not_in_db = pc.productcheckentry_set.get(input_product_id="Test")
        assert not_in_db.amount == 2
        assert not_in_db.in_database is False
        assert not_in_db.product_in_database is None
        assert not_in_db.part_of_product_list == ""
        assert not_in_db.migration_product is None

        # run again with a specific migration source (should perform the product check as normal)
        pc.migration_source = pms2  # use the less preferred migration source

        pc.perform_product_check()
        assert pc.productcheckentry_set.count() == 2

        in_db = pc.productcheckentry_set.get(input_product_id="myprod")
        assert in_db.amount == 4
        assert in_db.in_database is True
        assert in_db.product_in_database is not None
        assert in_db.part_of_product_list == pl2.hash + "\n" + pl.hash
        assert in_db.migration_product.replacement_product_id == pmo2.replacement_product_id

        not_in_db = pc.productcheckentry_set.get(input_product_id="Test")
        assert not_in_db.amount == 2
        assert not_in_db.in_database is False
        assert not_in_db.product_in_database is None
        assert not_in_db.part_of_product_list == ""
        assert not_in_db.migration_product is None

    def test_recursive_product_check_with_less_preferred_migration_source(self):
        """test recursive Product Check with specific less preferred migration source"""
        test_product_string = "myprod"
        test_list = "myprod;myprod\nmyprod;myprod\n" \
                    "Test;Test"
        p = mixer.blend(
            "productdb.Product",
            product_id=test_product_string,
            vendor=Vendor.objects.get(id=1),
            eox_update_time_stamp=_datetime.datetime.utcnow(),
            eol_ext_announcement_date=_datetime.date(2016, 1, 1),
            end_of_sale_date=_datetime.date(2016, 1, 1)
        )
        p2 = mixer.blend(
            "productdb.Product",
            product_id="replacement_pid",
            vendor=Vendor.objects.get(id=1),
            eox_update_time_stamp=_datetime.datetime.utcnow(),
            eol_ext_announcement_date=_datetime.date(2016, 1, 1),
            end_of_sale_date=_datetime.date(2016, 1, 1)
        )
        mixer.blend(
            "productdb.Product",
            product_id="another_replacement_pid",
            vendor=Vendor.objects.get(id=1)
        )
        pms = mixer.blend("productdb.ProductMigrationSource", name="Preferred Migration Source", preference=25)
        mixer.blend("productdb.ProductMigrationOption", product=p, migration_source=pms,
                    replacement_product_id="replacement_pid")
        mixer.blend("productdb.ProductMigrationOption", product=p2, migration_source=pms,
                    replacement_product_id="another_replacement_pid")
        pl = mixer.blend(
            "productdb.ProductList",
            name="TestList",
            string_product_list="myprod"
        )
        pl2 = mixer.blend(
            "productdb.ProductList",
            name="AnotherTestList",
            string_product_list="myprod"
        )

        pc = ProductCheck.objects.create(name="Test", input_product_ids=test_list, migration_source=pms)
        pc.perform_product_check()
        assert pc.productcheckentry_set.count() == 2

        in_db = pc.productcheckentry_set.get(input_product_id="myprod")
        assert in_db.amount == 4
        assert in_db.in_database is True
        assert in_db.product_in_database is not None
        assert in_db.part_of_product_list == pl2.hash + "\n" + pl.hash
        assert in_db.migration_product.replacement_product_id == "another_replacement_pid"  # use the last element in the path

        pl_names = in_db.get_product_list_names()
        assert len(pl_names) == 2
        assert "AnotherTestList" in pl_names
        assert "TestList" in pl_names

        not_in_db = pc.productcheckentry_set.get(input_product_id="Test")
        assert not_in_db.amount == 2
        assert not_in_db.in_database is False
        assert not_in_db.product_in_database is None
        assert not_in_db.part_of_product_list == ""
        assert not_in_db.migration_product is None


@pytest.mark.usefixtures("import_default_vendors")
class TestProductMigrationOption:
    def test_model(self):
        test_product_id = "My Product ID"
        replacement_product_id = "replaced product"
        p = mixer.blend(
            "productdb.Product",
            product_id=test_product_id,
            vendor=Vendor.objects.get(id=1)
        )
        repl_p = mixer.blend("productdb.Product", product_id=replacement_product_id)
        promiggrp = ProductMigrationSource.objects.create(name="Test")

        with pytest.raises(ValidationError) as exinfo:
            ProductMigrationOption.objects.create(
                migration_source=promiggrp
            )

        assert exinfo.match("\'product\': \[\'This field cannot be null.\'\]")

        with pytest.raises(ValidationError) as exinfo:
            ProductMigrationOption.objects.create(
                product=p
            )

        assert exinfo.match("\'migration_source\': \[\'This field cannot be null.\'\]")

        # test replacement_product_id with a product ID that is not in the database
        pmo = ProductMigrationOption.objects.create(
            product=p,
            migration_source=promiggrp,
            replacement_product_id="Missing Product"
        )

        assert pmo.is_replacement_in_db() is False
        assert pmo.get_product_replacement_id() is None
        assert pmo.is_valid_replacement() is True
        assert pmo.get_valid_replacement_product() is None
        assert str(pmo) == "replacement option for %s" % p.product_id
        pmo.delete()

        # test replacement_product_id with a product ID that is in the database
        pmo2 = ProductMigrationOption.objects.create(
            product=p,
            migration_source=promiggrp,
            replacement_product_id=replacement_product_id
        )

        assert pmo2.is_valid_replacement() is True
        assert pmo2.is_replacement_in_db() is True
        assert pmo2.get_product_replacement_id() == repl_p.id
        assert pmo2.get_valid_replacement_product().id == repl_p.id
        assert pmo2.get_valid_replacement_product().product_id == replacement_product_id

        # test replacement_product_id with a product ID that is in the database but EoL announced
        p = mixer.blend(
            "productdb.Product",
            product_id="eol_product",
            vendor=Vendor.objects.get(id=1),
            eox_update_time_stamp=_datetime.datetime.utcnow(),
            eol_ext_announcement_date=_datetime.date(2016, 1, 1),
            end_of_sale_date=_datetime.date(2016, 1, 1)
        )
        mixer.blend(
            "productdb.Product",
            product_id="replacement_eol_product",
            vendor=Vendor.objects.get(id=1),
            eox_update_time_stamp=_datetime.datetime.utcnow(),
            eol_ext_announcement_date=_datetime.date(2016, 1, 1),
            end_of_sale_date=_datetime.date(2016, 1, 1)
        )
        assert p.current_lifecycle_states == [Product.END_OF_SALE_STR]

        pmo3 = ProductMigrationOption.objects.create(
            product=p,
            migration_source=promiggrp,
            replacement_product_id="replacement_eol_product",
        )

        assert pmo3.is_valid_replacement() is False, "Should be False, because the product is EoL announced"
        assert pmo3.is_replacement_in_db() is True
        assert pmo3.get_valid_replacement_product() is None

    def test_unique_together_constraint(self):
        p = mixer.blend(
            "productdb.Product",
            product_id="Product",
            vendor=Vendor.objects.get(id=1)
        )
        promiggrp = ProductMigrationSource.objects.create(name="Test")
        ProductMigrationOption.objects.create(migration_source=promiggrp, product=p)

        with pytest.raises(ValidationError) as exinfo:
            ProductMigrationOption.objects.create(migration_source=promiggrp, product=p)

        assert exinfo.match("Product Migration Option with this Product and Migration source already exists.")

    def test_product_migration_group_set(self):
        test_product_id = "My Product ID"
        p = mixer.blend(
            "productdb.Product",
            product_id=test_product_id,
            vendor=Vendor.objects.get(id=1)
        )
        assert p.get_product_migration_source_names_set() == []

        promiggrp = ProductMigrationSource.objects.create(name="Test")
        ProductMigrationOption.objects.create(
            product=p,
            migration_source=promiggrp,
            replacement_product_id="Missing Product"
        )
        p.refresh_from_db()

        assert p.get_product_migration_source_names_set() == ["Test"]

        # test with additional migration group
        promiggrp2 = ProductMigrationSource.objects.create(name="Test 2")
        ProductMigrationOption.objects.create(
            product=p,
            migration_source=promiggrp2,
            replacement_product_id="Additional Missing Product"
        )
        p.refresh_from_db()

        assert p.get_product_migration_source_names_set() == ["Test", "Test 2"]

    def test_no_migration_option_provided_in_product(self):
        test_product_id = "My Product ID"
        p = mixer.blend(
            "productdb.Product",
            product_id=test_product_id,
            vendor=Vendor.objects.get(id=1)
        )

        assert p.has_migration_options() is False
        assert p.get_preferred_replacement_option() is None

    def test_single_valid_migration_option_provided_in_product(self):
        test_product_id = "My Product ID"
        p = mixer.blend(
            "productdb.Product",
            product_id=test_product_id,
            vendor=Vendor.objects.get(id=1)
        )
        promiggrp = ProductMigrationSource.objects.create(name="Test")
        pmo = ProductMigrationOption.objects.create(
            product=p,
            migration_source=promiggrp,
            replacement_product_id="Missing Product"
        )

        p.refresh_from_db()

        assert p.has_migration_options() is True
        assert p.get_preferred_replacement_option() == pmo
        assert pmo.is_valid_replacement() is True

    def test_single_valid_migration_option_provided_in_product_without_replacement_id(self):
        test_product_id = "My Product ID"
        p = mixer.blend(
            "productdb.Product",
            product_id=test_product_id,
            vendor=Vendor.objects.get(id=1)
        )
        promiggrp = ProductMigrationSource.objects.create(name="Test")
        pmo = ProductMigrationOption.objects.create(
            product=p,
            migration_source=promiggrp
        )

        p.refresh_from_db()

        assert p.has_migration_options() is True
        assert p.get_preferred_replacement_option() == pmo
        assert pmo.is_valid_replacement() is False

    def test_multiple_migration_options_provided_in_product(self):
        test_product_id = "My Product ID"
        p = mixer.blend(
            "productdb.Product",
            product_id=test_product_id,
            vendor=Vendor.objects.get(id=1)
        )
        promiggrp = ProductMigrationSource.objects.create(name="Test")
        preferred_promiggrp = ProductMigrationSource.objects.create(name="Test2", preference=100)
        pmo = ProductMigrationOption.objects.create(
            product=p,
            migration_source=promiggrp,
            replacement_product_id="Missing Product"
        )
        pmo2 = ProductMigrationOption.objects.create(
            product=p,
            migration_source=preferred_promiggrp,
            replacement_product_id="Another Missing Product"
        )

        p.refresh_from_db()

        assert p.has_migration_options() is True
        assert p.get_preferred_replacement_option() != pmo
        assert p.get_preferred_replacement_option() == pmo2
        assert pmo.is_valid_replacement() is True, "It is also a valid migration option, even if not the preferred one"
        assert pmo2.is_valid_replacement() is True

    def test_get_migration_path(self):
        # create basic object structure
        group1 = ProductMigrationSource.objects.create(name="Group One")
        group2 = ProductMigrationSource.objects.create(name="Group Two", preference=100)
        root_product = mixer.blend(
            "productdb.Product",
            product_id="C2960XS",
            vendor=Vendor.objects.get(id=1)
        )
        p11 = mixer.blend(
            "productdb.Product",
            product_id="C2960XL",
            vendor=Vendor.objects.get(id=1)
        )
        p12 = mixer.blend(
            "productdb.Product",
            product_id="C2960XT",
            vendor=Vendor.objects.get(id=1)
        )
        p23 = mixer.blend(
            "productdb.Product",
            product_id="C2960XR",
            vendor=Vendor.objects.get(id=1)
        )
        # root is replaced by 11 by Group One and by 12 by Group Two
        ProductMigrationOption.objects.create(
            product=root_product,
            migration_source=group1,
            replacement_product_id=p11.product_id
        )
        ProductMigrationOption.objects.create(
            product=root_product,
            migration_source=group2,
            replacement_product_id=p12.product_id
        )
        # p12 is replaced by 23 by group 2
        ProductMigrationOption.objects.create(
            product=p12,
            migration_source=group2,
            replacement_product_id=p23.product_id
        )

        # get the preferred group for the root product
        assert root_product.get_preferred_replacement_option().migration_source.name == group2.name

        # get the new migration path for the preferred group
        group2_migrations = root_product.get_migration_path()

        expected_replacement_paths_and_order = ["C2960XT"]
        read_list = [e.replacement_product_id for e in group2_migrations]
        assert len(group2_migrations) == 1
        assert group2_migrations[0].migration_source.name == "Group Two"
        assert expected_replacement_paths_and_order == read_list

        # the replacement option is now end of life
        p12.eol_ext_announcement_date = _datetime.date(2016, 1, 1)
        p12.end_of_sale_date = _datetime.date(2016, 1, 1)
        p12.save()

        # get the new migration path for the preferred group
        group2_migrations = root_product.get_migration_path()

        expected_replacement_paths_and_order = ["C2960XT", "C2960XR"]
        read_list = [e.replacement_product_id for e in group2_migrations]
        assert len(group2_migrations) == 2
        assert group2_migrations[0].migration_source.name == "Group Two"
        assert expected_replacement_paths_and_order == read_list

        # test with valid product (empty list is expected)
        p11_preferred_migration = p11.get_migration_path()
        assert p11_preferred_migration == []

        # get the migration path for the other group
        group1_migration = root_product.get_migration_path(group1.name)
        expected_replacement_paths_and_order = ["C2960XL"]
        read_list = [e.replacement_product_id for e in group1_migration]
        assert len(group1_migration) == 1
        assert expected_replacement_paths_and_order == read_list

        # test invalid call
        with pytest.raises(AttributeError):
            p11.get_migration_path(123)

    def test_replacement_id_cannot_be_the_product_id_of_the_entry(self):
        expected_error = "{'replacement_product_id': \['Product ID that should be replaced cannot be the same as the " \
                         "suggested replacement Product ID'\]}"

        # create basic object structure
        group1 = ProductMigrationSource.objects.create(name="Group One")
        root_product = mixer.blend(
            "productdb.Product",
            product_id="C2960XS",
            vendor=Vendor.objects.get(id=1)
        )

        with pytest.raises(ValidationError) as exinfo:
            ProductMigrationOption.objects.create(
                product=root_product,
                migration_source=group1,
                replacement_product_id=root_product.product_id
            )
        assert exinfo.match(expected_error)

        pmo = ProductMigrationOption.objects.create(
            product=root_product,
            migration_source=group1,
            replacement_product_id="Not in Database"
        )

        with pytest.raises(ValidationError) as exinfo:
            pmo.replacement_product_id = root_product.product_id
            pmo.save()
        assert exinfo.match(expected_error)

    def test_update_replacement_db_product_field_in_product_migration_options(self):
        # create basic object structure
        group1 = ProductMigrationSource.objects.create(name="Group One")
        root_product = mixer.blend(
            "productdb.Product",
            product_id="C2960XS",
            vendor=Vendor.objects.get(id=1)
        )
        p11 = mixer.blend(
            "productdb.Product",
            product_id="C2960XL",
            vendor=Vendor.objects.get(id=1)
        )
        p12 = mixer.blend(
            "productdb.Product",
            product_id="C2960XT",
            vendor=Vendor.objects.get(id=1)
        )

        # add first replacement with a valid database option
        pmo1 = ProductMigrationOption.objects.create(
            product=root_product,
            migration_source=group1,
            replacement_product_id=p11.product_id
        )

        assert pmo1.is_replacement_in_db() is True
        assert pmo1.get_product_replacement_id() == p11.id
        assert pmo1.replacement_db_product == p11

        # create a cascade
        pmo2 = ProductMigrationOption.objects.create(
            product=p11,
            migration_source=group1,
            replacement_product_id=p12.product_id
        )

        assert pmo2.is_replacement_in_db() is True
        assert pmo2.get_product_replacement_id() == p12.id
        assert pmo2.replacement_db_product == p12

        # create a replacement product ID that is not part of the database for p12
        pmo3 = ProductMigrationOption.objects.create(
            product=p12,
            migration_source=group1,
            replacement_product_id="Not in the database"
        )

        assert pmo3.is_replacement_in_db() is False
        assert pmo3.get_product_replacement_id() is None
        assert pmo3.replacement_db_product is None

        # drop p11 form database
        p11.delete()

        # update objects from DB, the migration chain is broken after the first migration option (because p11 will
        # delete pmo2, bus pmo1 drops only the foreign key
        pmo1.refresh_from_db()
        with pytest.raises(ProductMigrationOption.DoesNotExist):
            pmo2.refresh_from_db()
        pmo3.refresh_from_db()

        assert pmo1.is_replacement_in_db() is False
        assert pmo1.get_product_replacement_id() is None
        assert pmo1.replacement_db_product is None
        assert pmo1.replacement_product_id == p11.product_id

        assert pmo3.is_replacement_in_db() is False
        assert pmo3.get_product_replacement_id() is None
        assert pmo3.replacement_db_product is None


@pytest.mark.usefixtures("import_default_vendors")
class TestProductIdNormalization:
    def test_model(self):
        v1 = Vendor.objects.get(id=1)
        pnr = ProductIdNormalizationRule.objects.create(
            vendor=v1,
            product_id="PWR-C1-715WAC=",
            regex_match=r"^PWR\-C1\-715WAC$"
        )

        assert pnr.matches("PWR-C1-715WAC") is True
        assert pnr.matches("PWR-C1-715WA") is False
        assert pnr.matches("") is False
        assert pnr.get_normalized_product_id("PWR-C1-715WAC") == "PWR-C1-715WAC="

        pnr2 = ProductIdNormalizationRule.objects.create(
            vendor=v1,
            product_id="PWR-C1-%sWAC=",
            regex_match=r"^PWR\-C1\-(\d+)WAC$"
        )

        assert pnr2.matches("PWR-C1-715WAC") is True
        assert pnr2.matches("PWR-C1-715WA") is False
        assert pnr2.matches("") is False
        assert pnr2.get_normalized_product_id("PWR-C1-715WAC") == "PWR-C1-715WAC="

        with pytest.raises(ValidationError):
            ProductIdNormalizationRule.objects.create(
                vendor=v1,
                product_id="PWR-C1-715WAC=",
                regex_match=r"^PWR\-C1\-715WAC$",
                comment="duplicated entry"
            )
