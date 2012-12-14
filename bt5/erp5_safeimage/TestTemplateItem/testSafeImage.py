#from Products.ERP5.Document.Image import Image
#from Products.ERP5Type.tests.utils import FileUpload
import Image
from Products.ERP5Type.tests.ERP5TypeTestCase import ERP5TypeTestCase
import transaction
from zLOG import LOG,INFO,ERROR 
import json
from cStringIO import StringIO
import os


class FileUpload(file):
  """Act as an uploaded file.
  """
  __allow_access_to_unprotected_subobjects__ = 1
  def __init__(self, path, name):
    self.filename = name
    file.__init__(self, path)
    self.headers = {}


def makeFilePath(name):
  return os.path.join(os.path.dirname(__file__), 'tmp', name)

def makeFileUpload(name, as_name=None):
  if as_name is None:
    as_name = name
  path = makeFilePath(name)
  return FileUpload(path, as_name)

class TestSafeImage(ERP5TypeTestCase):

  def getBusinessTemplateList(self):
    return ('erp5_base',
            'erp5_dms',
            'erp5_safeimage'
           )

  def afterSetUp(self):
    portal = self.getPortalObject()
    self.image_module = self.portal.getDefaultModule(portal_type = 'Image Module')
    self.assertTrue(self.image_module is not None)
    if getattr(self.image_module,'testImage',None) is not None:
      self.image_module.manage_delObjects(ids=['testImage'])
    if getattr(self.image_module,'testTile',None) is not None:
      self.image_module.manage_delObjects(ids=['testTile'])
    if getattr(self.image_module,'testTileTransformed',None) is not None:
      self.image_module.manage_delObjects(ids=['testTileTransformed'])
    transaction.commit()
    self.tic()

  def _createImage(self):
    portal = self.getPortalObject()
    _image = makeFileUpload('image_test.jpg')
    image = self.image_module.newContent(portal_type='Image',title='testImage',
                                id='testImage',file=_image,filename='testImage')
    return image

  def _createTileImage(self):
    portal = self.getPortalObject()
    tile_image = makeFileUpload('image_test.jpg')
    tile = self.image_module.newContent(portal_type='Image Tile',title='testTile',
                             id='testTile',file=tile_image,filename='testTile')
    return tile 

  def _createTileImageTransformed(self):
    portal = self.getPortalObject()
    tile_image_transformed = makeFileUpload('image_test.jpg')
    tile_transformed = self.image_module.newContent(portal_type='Image Tile Transformed',
                             title='testTileTransformed',id='testTileTransformed',
                             file=tile_image_transformed,filename='testTileTransformed')
    return tile_transformed 

  def test_01_CreateImage(self):
    image = self._createImage()
    self.assertTrue(image.hasData())
    transaction.commit()
    self.tic()
    self.assertNotEqual(image,None) 

  def test_02_CreateTileImage(self):
     """"
     We are going to check that tile image has following structure
     1/
     1/Image Tile Group
     1/Image Tile Group/0-0-0
     1/Image Tile Group/1-0-0
     1/ImageProperties.xml
     """
     tile = self._createTileImage()
     transaction.commit()
     self.tic()
     self.assertNotEqual(tile,None)
     image_property = getattr(tile, "ImageProperties.xml", None)
     self.assertEquals(image_property.getData(),
 """<IMAGE_PROPERTIES WIDTH="660" HEIGHT="495" NUMTILES="9" NUMIMAGES="1" VERSION="1.8" TILESIZE="256" />""")
     self.assertNotEqual(image_property, None)
     self.assertEquals("Embedded File", image_property.getPortalType())
     image_group = getattr(tile, "TileGroup0", None)
     self.assertNotEquals(image_group, None)
     self.assertEquals("Image Tile Group",image_group.getPortalType())
     splitted_image_list = image_group.objectValues(portal_type="Image")
     self.assertEquals(set(['0-0-0','1-0-0','1-1-0','2-0-0','2-0-1','2-1-0','2-1-1','2-2-0','2-2-1']),
                       set([x.getId() for x in splitted_image_list]))
     for x in splitted_image_list:
        self.assertTrue(x.hasData())
     self.assertEquals(123,image_group['0-0-0'].getHeight()) 
     self.assertEquals(165,image_group['0-0-0'].getWidth()) 

  def test_03_CreateTileImageTransformed(self):
     """"
     We are going to check that tile image has following structure
     1/
     1/Image Tile Group
     1/Image Tile Group/0-0-0
     1/Image Tile Group/1-0-0
     1/ImageProperties.xml
     1/TransformFile.txt
     """
     tile_transformed = self._createTileImageTransformed()
     transaction.commit()
     self.tic()
     self.assertNotEqual(tile_transformed,None)
     image_property = getattr(tile_transformed, "ImageProperties.xml", None)
     self.assertEquals(image_property.getData(),
 """<IMAGE_PROPERTIES WIDTH="660" HEIGHT="495" NUMTILES="9" NUMIMAGES="1" VERSION="1.8" TILESIZE="256" />""")
     self.assertNotEqual(image_property, None)
     self.assertEquals("Embedded File", image_property.getPortalType())
     image_transform = getattr(tile_transformed, "TransformFile.txt", None)
     self.assertTrue(image_transform.getData().split()[1],'2-0-0')
     self.assertNotEqual(image_transform, None)
     self.assertEquals("Embedded File", image_transform.getPortalType())
     image_group = getattr(tile_transformed, "TileGroup0", None)
     self.assertNotEquals(image_group, None)
     self.assertEquals("Image Tile Group",image_group.getPortalType())
     splitted_image_list = image_group.objectValues(portal_type="Image")
     self.assertEquals(set(['0-0-0','1-0-0','1-1-0','2-0-0','2-0-1','2-1-0','2-1-1','2-2-0','2-2-1']),
                       set([x.getId() for x in splitted_image_list]))
     for x in splitted_image_list:
        self.assertTrue(x.hasData())
     self.assertEquals(123,image_group['0-0-0'].getHeight()) 
     self.assertEquals(165,image_group['0-0-0'].getWidth())
     if getattr(self.image_module,'testTileTransformed',None) is not None:
      self.image_module.manage_delObjects(ids=['testTileTransformed'])
     transaction.commit()
     self.tic()
