import os
from io import BytesIO

import pytest

from PyPDF2 import PageObject, PdfMerger, PdfReader, PdfWriter
from PyPDF2.errors import PageSizeNotDefinedError
from PyPDF2.generic import RectangleObject, StreamObject

from . import get_pdf_from_url

TESTS_ROOT = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.dirname(TESTS_ROOT)
RESOURCE_ROOT = os.path.join(PROJECT_ROOT, "resources")


def test_writer_clone():
    src = os.path.join(RESOURCE_ROOT, "pdflatex-outline.pdf")

    reader = PdfReader(src)
    writer = PdfWriter()

    writer.clone_document_from_reader(reader)
    assert len(writer.pages) == 4


def test_writer_operations():
    """
    This test just checks if the operation throws an exception.

    This should be done way more thoroughly: It should be checked if the
    output is as expected.
    """
    pdf_path = os.path.join(RESOURCE_ROOT, "crazyones.pdf")
    pdf_outline_path = os.path.join(RESOURCE_ROOT, "pdflatex-outline.pdf")

    reader = PdfReader(pdf_path)
    reader_outline = PdfReader(pdf_outline_path)

    writer = PdfWriter()
    page = reader.pages[0]
    with pytest.raises(PageSizeNotDefinedError) as exc:
        writer.add_blank_page()
    assert exc.value.args == ()
    writer.insert_page(page, 1)
    writer.insert_page(reader_outline.pages[0], 0)
    writer.add_bookmark_destination(page)
    writer.remove_links()
    writer.add_bookmark_destination(page)
    bm = writer.add_bookmark(
        "A bookmark", 0, None, (255, 0, 15), True, True, "/FitBV", 10
    )
    writer.add_bookmark(
        "The XYZ fit", 0, bm, (255, 0, 15), True, True, "/XYZ", 10, 20, 3
    )
    writer.add_bookmark("The FitH fit", 0, bm, (255, 0, 15), True, True, "/FitH", 10)
    writer.add_bookmark("The FitV fit", 0, bm, (255, 0, 15), True, True, "/FitV", 10)
    writer.add_bookmark(
        "The FitR fit", 0, bm, (255, 0, 15), True, True, "/FitR", 10, 20, 30, 40
    )
    writer.add_bookmark("The FitB fit", 0, bm, (255, 0, 15), True, True, "/FitB")
    writer.add_bookmark("The FitBH fit", 0, bm, (255, 0, 15), True, True, "/FitBH", 10)
    writer.add_bookmark("The FitBV fit", 0, bm, (255, 0, 15), True, True, "/FitBV", 10)
    writer.add_blank_page()
    writer.add_uri(2, "https://example.com", RectangleObject([0, 0, 100, 100]))
    writer.add_link(2, 1, RectangleObject([0, 0, 100, 100]))
    assert writer._get_page_layout() is None
    writer._set_page_layout("/SinglePage")
    assert writer._get_page_layout() == "/SinglePage"
    assert writer._get_page_mode() is None
    writer.set_page_mode("/UseNone")
    assert writer._get_page_mode() == "/UseNone"
    writer.insert_blank_page(width=100, height=100)
    writer.insert_blank_page()  # without parameters

    # TODO: This gives "KeyError: '/Contents'" - is that a bug?
    # writer.removeImages()

    writer.add_metadata({"author": "Martin Thoma"})

    writer.add_attachment("foobar.gif", b"foobarcontent")

    # finally, write "output" to PyPDF2-output.pdf
    tmp_path = "dont_commit_writer.pdf"
    with open(tmp_path, "wb") as output_stream:
        writer.write(output_stream)

    # Check that every key in _idnum_hash is correct
    objects_hash = [o.hash_value() for o in writer._objects]
    for k, v in writer._idnum_hash.items():
        assert v.pdf == writer
        assert k in objects_hash, "Missing %s" % v

    # cleanup
    os.remove(tmp_path)


@pytest.mark.parametrize(
    ("input_path", "ignore_byte_string_object"),
    [
        ("side-by-side-subfig.pdf", False),
        ("reportlab-inline-image.pdf", True),
    ],
)
def test_remove_images(input_path, ignore_byte_string_object):
    pdf_path = os.path.join(RESOURCE_ROOT, input_path)

    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    page = reader.pages[0]
    writer.insert_page(page, 0)
    writer.remove_images(ignore_byte_string_object=ignore_byte_string_object)

    # finally, write "output" to PyPDF2-output.pdf
    tmp_filename = "dont_commit_writer_removed_image.pdf"
    with open(tmp_filename, "wb") as output_stream:
        writer.write(output_stream)

    with open(tmp_filename, "rb") as input_stream:
        reader = PdfReader(input_stream)
        if input_path == "side-by-side-subfig.pdf":
            extracted_text = reader.pages[0].extract_text()
            assert "Lorem ipsum dolor sit amet" in extracted_text

    # Cleanup
    os.remove(tmp_filename)


@pytest.mark.parametrize(
    ("input_path", "ignore_byte_string_object"),
    [
        ("side-by-side-subfig.pdf", False),
        ("side-by-side-subfig.pdf", True),
        ("reportlab-inline-image.pdf", False),
        ("reportlab-inline-image.pdf", True),
    ],
)
def test_remove_text(input_path, ignore_byte_string_object):
    pdf_path = os.path.join(RESOURCE_ROOT, input_path)

    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    page = reader.pages[0]
    writer.insert_page(page, 0)
    writer.remove_text(ignore_byte_string_object=ignore_byte_string_object)

    # finally, write "output" to PyPDF2-output.pdf
    tmp_filename = "dont_commit_writer_removed_text.pdf"
    with open(tmp_filename, "wb") as output_stream:
        writer.write(output_stream)

    # Cleanup
    os.remove(tmp_filename)


@pytest.mark.parametrize(
    ("ignore_byte_string_object"),
    [False, True],
)
def test_remove_text_all_operators(ignore_byte_string_object):
    stream = (
        b"BT "
        b"/F0 36 Tf "
        b"50 706 Td "
        b"36 TL "
        b"(The Tj operator) Tj "
        b'1 2 (The double quote operator) " '
        b"(The single quote operator) ' "
        b"ET"
    )
    pdf_data = (
        b"%%PDF-1.7\n"
        b"1 0 obj << /Count 1 /Kids [5 0 R] /Type /Pages >> endobj\n"
        b"2 0 obj << >> endobj\n"
        b"3 0 obj << >> endobj\n"
        b"4 0 obj << /Length %d >>\n"
        b"stream\n" + (b"%s\n" % stream) + b"endstream\n"
        b"endobj\n"
        b"5 0 obj << /Contents 4 0 R /CropBox [0.0 0.0 2550.0 3508.0]\n"
        b" /MediaBox [0.0 0.0 2550.0 3508.0] /Parent 1 0 R"
        b" /Resources << /Font << >> >>"
        b" /Rotate 0 /Type /Page >> endobj\n"
        b"6 0 obj << /Pages 1 0 R /Type /Catalog >> endobj\n"
        b"xref 1 6\n"
        b"%010d 00000 n\n"
        b"%010d 00000 n\n"
        b"%010d 00000 n\n"
        b"%010d 00000 n\n"
        b"%010d 00000 n\n"
        b"%010d 00000 n\n"
        b"trailer << /Root 6 0 R /Size 6 >>\n"
        b"startxref\n%d\n"
        b"%%%%EOF"
    )
    startx_correction = -1
    pdf_data = pdf_data % (
        len(stream),
        pdf_data.find(b"1 0 obj") + startx_correction,
        pdf_data.find(b"2 0 obj") + startx_correction,
        pdf_data.find(b"3 0 obj") + startx_correction,
        pdf_data.find(b"4 0 obj") + startx_correction,
        pdf_data.find(b"5 0 obj") + startx_correction,
        pdf_data.find(b"6 0 obj") + startx_correction,
        # startx_correction should be -1 due to double % at the beginning indiducing an error on startxref computation
        pdf_data.find(b"xref"),
    )
    print(pdf_data.decode())
    pdf_stream = BytesIO(pdf_data)

    reader = PdfReader(pdf_stream, strict=False)
    writer = PdfWriter()

    page = reader.pages[0]
    writer.insert_page(page, 0)
    writer.remove_text(ignore_byte_string_object=ignore_byte_string_object)

    # finally, write "output" to PyPDF2-output.pdf
    tmp_filename = "dont_commit_writer_removed_text.pdf"
    with open(tmp_filename, "wb") as output_stream:
        writer.write(output_stream)

    # Cleanup
    os.remove(tmp_filename)


def test_write_metadata():
    pdf_path = os.path.join(RESOURCE_ROOT, "crazyones.pdf")

    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    metadata = reader.metadata
    writer.add_metadata(metadata)

    writer.add_metadata({"/Title": "The Crazy Ones"})

    # finally, write data to PyPDF2-output.pdf
    tmp_filename = "dont_commit_writer_added_metadata.pdf"
    with open(tmp_filename, "wb") as output_stream:
        writer.write(output_stream)

    # Check if the title was set
    reader = PdfReader(tmp_filename)
    metadata = reader.metadata
    assert metadata.get("/Title") == "The Crazy Ones"

    # Cleanup
    os.remove(tmp_filename)


def test_fill_form():
    reader = PdfReader(os.path.join(RESOURCE_ROOT, "form.pdf"))
    writer = PdfWriter()

    page = reader.pages[0]

    writer.add_page(page)

    writer.update_page_form_field_values(
        writer.pages[0], {"foo": "some filled in text"}, flags=1
    )

    # write "output" to PyPDF2-output.pdf
    tmp_filename = "dont_commit_filled_pdf.pdf"
    with open(tmp_filename, "wb") as output_stream:
        writer.write(output_stream)


@pytest.mark.parametrize(
    "use_128bit",
    [(True), (False)],
)
def test_encrypt(use_128bit):
    reader = PdfReader(os.path.join(RESOURCE_ROOT, "form.pdf"))
    writer = PdfWriter()

    page = reader.pages[0]
    orig_text = page.extract_text()

    writer.add_page(page)
    writer.encrypt(user_pwd="userpwd", owner_pwd="ownerpwd", use_128bit=use_128bit)

    # write "output" to PyPDF2-output.pdf
    tmp_filename = "dont_commit_encrypted.pdf"
    with open(tmp_filename, "wb") as output_stream:
        writer.write(output_stream)

    with open(tmp_filename, "rb") as input_stream:
        data = input_stream.read()

    assert b"foo" not in data

    reader = PdfReader(tmp_filename, password="userpwd")
    new_text = reader.pages[0].extract_text()
    assert reader.metadata.get("/Producer") == "PyPDF2"

    assert new_text == orig_text

    # Cleanup
    os.remove(tmp_filename)


def test_add_bookmark():
    reader = PdfReader(os.path.join(RESOURCE_ROOT, "pdflatex-outline.pdf"))
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    bookmark = writer.add_bookmark(
        "A bookmark", 1, None, (255, 0, 15), True, True, "/Fit", 200, 0, None
    )
    writer.add_bookmark("Another", 2, bookmark, None, False, False, "/Fit", 0, 0, None)

    # write "output" to PyPDF2-output.pdf
    tmp_filename = "dont_commit_bookmark.pdf"
    with open(tmp_filename, "wb") as output_stream:
        writer.write(output_stream)

    # Cleanup
    os.remove(tmp_filename)


def test_add_named_destination():
    reader = PdfReader(os.path.join(RESOURCE_ROOT, "pdflatex-outline.pdf"))
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    from PyPDF2.generic import NameObject

    writer.add_named_destination(NameObject("A named dest"), 2)
    writer.add_named_destination(NameObject("A named dest2"), 2)

    from PyPDF2.generic import IndirectObject

    assert writer.get_named_dest_root() == [
        "A named dest",
        IndirectObject(7, 0, writer),
        "A named dest2",
        IndirectObject(10, 0, writer),
    ]

    # write "output" to PyPDF2-output.pdf
    tmp_filename = "dont_commit_named_destination.pdf"
    with open(tmp_filename, "wb") as output_stream:
        writer.write(output_stream)

    # Cleanup
    os.remove(tmp_filename)


def test_add_uri():
    reader = PdfReader(os.path.join(RESOURCE_ROOT, "pdflatex-outline.pdf"))
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    from PyPDF2.generic import RectangleObject

    writer.add_uri(
        1,
        "http://www.example.com",
        RectangleObject([0, 0, 100, 100]),
        border=[1, 2, 3, [4]],
    )
    writer.add_uri(
        2,
        "https://pypdf2.readthedocs.io/en/latest/",
        RectangleObject([20, 30, 50, 80]),
        border=[1, 2, 3],
    )
    writer.add_uri(
        3,
        "https://pypdf2.readthedocs.io/en/latest/user/adding-pdf-annotations.html",
        "[ 200 300 250 350 ]",
        border=[0, 0, 0],
    )
    writer.add_uri(
        3,
        "https://pypdf2.readthedocs.io/en/latest/user/adding-pdf-annotations.html",
        [100, 200, 150, 250],
        border=[0, 0, 0],
    )

    # write "output" to PyPDF2-output.pdf
    tmp_filename = "dont_commit_uri.pdf"
    with open(tmp_filename, "wb") as output_stream:
        writer.write(output_stream)

    # Cleanup
    os.remove(tmp_filename)


def test_add_link():
    reader = PdfReader(os.path.join(RESOURCE_ROOT, "pdflatex-outline.pdf"))
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    from PyPDF2.generic import RectangleObject

    writer.add_link(
        1,
        2,
        RectangleObject([0, 0, 100, 100]),
        border=[1, 2, 3, [4]],
        fit="/Fit",
    )
    writer.add_link(2, 3, RectangleObject([20, 30, 50, 80]), [1, 2, 3], "/FitH", None)
    writer.add_link(
        3,
        0,
        "[ 200 300 250 350 ]",
        [0, 0, 0],
        "/XYZ",
        0,
        0,
        2,
    )
    writer.add_link(
        3,
        0,
        [100, 200, 150, 250],
        border=[0, 0, 0],
    )

    # write "output" to PyPDF2-output.pdf
    tmp_filename = "dont_commit_link.pdf"
    with open(tmp_filename, "wb") as output_stream:
        writer.write(output_stream)

    # Cleanup
    os.remove(tmp_filename)


def test_io_streams():
    """This is the example from the docs ("Streaming data")."""

    filepath = os.path.join(RESOURCE_ROOT, "pdflatex-outline.pdf")
    with open(filepath, "rb") as fh:
        bytes_stream = BytesIO(fh.read())

    # Read from bytes stream
    reader = PdfReader(bytes_stream)
    assert len(reader.pages) == 4

    # Write to bytes stream
    writer = PdfWriter()
    with BytesIO() as output_stream:
        writer.write(output_stream)


def test_regression_issue670():
    filepath = os.path.join(RESOURCE_ROOT, "crazyones.pdf")
    reader = PdfReader(filepath, strict=False)
    for _ in range(2):
        writer = PdfWriter()
        writer.add_page(reader.pages[0])
        with open("dont_commit_issue670.pdf", "wb") as f_pdf:
            writer.write(f_pdf)


def test_issue301():
    """
    Test with invalid stream length object
    """
    with open(os.path.join(RESOURCE_ROOT, "issue-301.pdf"), "rb") as f:
        reader = PdfReader(f)
        writer = PdfWriter()
        writer.append_pages_from_reader(reader)
        o = BytesIO()
        writer.write(o)


def test_sweep_indirect_references_nullobject_exception():
    # TODO: Check this more closely... this looks weird
    url = "https://corpora.tika.apache.org/base/docs/govdocs1/924/924666.pdf"
    name = "tika-924666.pdf"
    reader = PdfReader(BytesIO(get_pdf_from_url(url, name=name)))
    merger = PdfMerger()
    merger.append(reader)
    merger.write("tmp-merger-do-not-commit.pdf")

    # cleanup
    os.remove("tmp-merger-do-not-commit.pdf")


def test_write_bookmark_on_page_fitv():
    url = "https://corpora.tika.apache.org/base/docs/govdocs1/922/922840.pdf"
    name = "tika-922840.pdf"
    reader = PdfReader(BytesIO(get_pdf_from_url(url, name=name)))
    merger = PdfMerger()
    merger.append(reader)
    merger.write("tmp-merger-do-not-commit.pdf")

    # cleanup
    os.remove("tmp-merger-do-not-commit.pdf")


def test_pdf_header():
    writer = PdfWriter()
    assert writer.pdf_header == b"%PDF-1.3"

    reader = PdfReader(os.path.join(RESOURCE_ROOT, "crazyones.pdf"))
    writer.add_page(reader.pages[0])
    assert writer.pdf_header == b"%PDF-1.5"

    writer.pdf_header = b"%PDF-1.6"
    assert writer.pdf_header == b"%PDF-1.6"


def test_write_dict_stream_object():
    stream = (
        b"BT "
        b"/F0 36 Tf "
        b"50 706 Td "
        b"36 TL "
        b"(The Tj operator) Tj "
        b'1 2 (The double quote operator) " '
        b"(The single quote operator) ' "
        b"ET"
    )
    from PyPDF2.generic import NameObject, IndirectObject

    stream_object = StreamObject()
    stream_object[NameObject("/Type")] = NameObject("/Text")
    stream_object._data = stream

    writer = PdfWriter()

    page_object = PageObject.create_blank_page(writer, 1000, 1000)
    # Construct dictionary object (PageObject) with stream object
    # Writer will replace this stream object with indirect object
    page_object[NameObject("/Test")] = stream_object

    writer.add_page(page_object)

    for k, v in page_object.items():
        if k == "/Test":
            assert str(v) == str(stream_object)
            break
    else:
        assert False, "/Test not found"

    with open("tmp-writer-do-not-commit.pdf", "wb") as fp:
        writer.write(fp)

    for k, v in page_object.items():
        if k == "/Test":
            assert str(v) != str(stream_object)
            assert isinstance(v, IndirectObject)
            assert str(v.get_object()) == str(stream_object)
            break
    else:
        assert False, "/Test not found"

    # Check that every key in _idnum_hash is correct
    objects_hash = [o.hash_value() for o in writer._objects]
    for k, v in writer._idnum_hash.items():
        assert v.pdf == writer
        assert k in objects_hash, "Missing %s" % v

    os.remove("tmp-writer-do-not-commit.pdf")
