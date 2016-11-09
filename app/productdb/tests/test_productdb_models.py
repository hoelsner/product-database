"""
Test suite for the productdb.models module
"""
import pytest
import os
import tempfile
import datetime
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files import File
from django.db.models import QuerySet
from mixer.backend.django import mixer
from app.productdb.models import Vendor, ProductList, JobFile, Product, UserProfile, ProductGroup, ProductMigrationSource, \
    ProductMigrationOption

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
        p.eox_update_time_stamp = datetime.datetime.now()
        assert p.current_lifecycle_states == [Product.NO_EOL_ANNOUNCEMENT_STR], "No EoX announcement found at this point"

        # set the eox announcement state
        p.eol_ext_announcement_date = datetime.date.today()
        expected_output = [Product.EOS_ANNOUNCED_STR]
        assert p.current_lifecycle_states == expected_output, "EoL announcement should be visible"

        # set the End of Sale date
        p.end_of_sale_date = datetime.date.today() + datetime.timedelta(days=1)
        expected_output = [Product.EOS_ANNOUNCED_STR]
        assert p.current_lifecycle_states == expected_output, \
            "Nothing should change, because the date is in the future"
        p.end_of_sale_date = datetime.date.today()
        expected_output = [Product.END_OF_SALE_STR]
        assert p.current_lifecycle_states == expected_output

        # set the End of new Service Attachment Date
        p.end_of_new_service_attachment_date = datetime.date.today() + datetime.timedelta(days=1)
        assert p.current_lifecycle_states == expected_output, \
            "Nothing should change, because the date is in the future"
        p.end_of_new_service_attachment_date = datetime.date.today()
        expected_output = [Product.END_OF_SALE_STR, Product.END_OF_NEW_SERVICE_ATTACHMENT_STR]
        assert p.current_lifecycle_states == expected_output

        # set the End of SW maintenance date
        p.end_of_sw_maintenance_date = datetime.date.today() + datetime.timedelta(days=1)
        assert p.current_lifecycle_states == expected_output, \
            "Nothing should change, because the date is in the future"
        p.end_of_sw_maintenance_date = datetime.date.today()
        expected_output = [
            Product.END_OF_SALE_STR,
            Product.END_OF_NEW_SERVICE_ATTACHMENT_STR,
            Product.END_OF_SW_MAINTENANCE_RELEASES_STR
        ]
        assert p.current_lifecycle_states == expected_output

        # set the End of Routine Failure Analysis date
        p.end_of_routine_failure_analysis = datetime.date.today() + datetime.timedelta(days=1)
        assert p.current_lifecycle_states == expected_output, \
            "Nothing should change, because the date is in the future"
        p.end_of_routine_failure_analysis = datetime.date.today()
        expected_output = [
            Product.END_OF_SALE_STR,
            Product.END_OF_NEW_SERVICE_ATTACHMENT_STR,
            Product.END_OF_SW_MAINTENANCE_RELEASES_STR,
            Product.END_OF_ROUTINE_FAILURE_ANALYSIS_STR
        ]
        assert p.current_lifecycle_states == expected_output

        # set the End of Service Contract Renewal date
        p.end_of_service_contract_renewal = datetime.date.today() + datetime.timedelta(days=1)
        assert p.current_lifecycle_states == expected_output, \
            "Nothing should change, because the date is in the future"
        p.end_of_service_contract_renewal = datetime.date.today()
        expected_output = [
            Product.END_OF_SALE_STR,
            Product.END_OF_NEW_SERVICE_ATTACHMENT_STR,
            Product.END_OF_SW_MAINTENANCE_RELEASES_STR,
            Product.END_OF_ROUTINE_FAILURE_ANALYSIS_STR,
            Product.END_OF_SERVICE_CONTRACT_RENEWAL_STR
        ]
        assert p.current_lifecycle_states == expected_output

        # set the End of Vulnerability/Security Support date
        p.end_of_sec_vuln_supp_date = datetime.date.today() + datetime.timedelta(days=1)
        assert p.current_lifecycle_states == expected_output, \
            "Nothing should change, because the date is in the future"
        p.end_of_sec_vuln_supp_date = datetime.date.today()
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
        p.end_of_support_date = datetime.date.today() + datetime.timedelta(days=1)
        assert p.current_lifecycle_states == expected_output, \
            "Nothing should change, because the date is in the future"
        p.end_of_support_date = datetime.date.today()
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

        assert exinfo.match("name': \['Product list with this Product List Name already exists.'")

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

        assert exinfo.match("\'name\': \[\'Product migration source with this Name already exists.\'\]")


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
            eox_update_time_stamp=datetime.datetime.utcnow(),
            eol_ext_announcement_date=datetime.date(2016, 1, 1),
            end_of_sale_date=datetime.date(2016, 1, 1)
        )
        mixer.blend(
            "productdb.Product",
            product_id="replacement_eol_product",
            vendor=Vendor.objects.get(id=1),
            eox_update_time_stamp=datetime.datetime.utcnow(),
            eol_ext_announcement_date=datetime.date(2016, 1, 1),
            end_of_sale_date=datetime.date(2016, 1, 1)
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

        assert exinfo.match("Product migration option with this Product and Migration source already exists.")

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
        p12.eol_ext_announcement_date = datetime.date(2016, 1, 1)
        p12.end_of_sale_date = datetime.date(2016, 1, 1)
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
