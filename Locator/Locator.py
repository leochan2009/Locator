import os
import unittest
import time
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import vtkSlicerOpenIGTLinkIFModuleMRML
from vtkSlicerOpenIGTLinkIFModuleMRML import vtkMRMLIGTLQueryNode
from slicer import vtkMRMLLinearTransformNode
from slicer import util
from time import sleep

#------------------------------------------------------------
#
# Locator
#
class Locator(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """
  
  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Locator" # TODO make this more human readable by adding spaces
    self.parent.categories = ["IGT"]
    self.parent.dependencies = []
    self.parent.contributors = ["Junichi Tokuda, Wei Wang, Ehud Schmidt, Longquan Chen (BWH)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
      A communication interface for Koh Young's 3D sensors.
      """
    self.parent.acknowledgementText = """
      This work is supported by NIH National Center for Image Guided Therapy (P41EB015898).
      """
# replace with organization, grant and thanks.


#------------------------------------------------------------
#
# LocatorWidget
#
class LocatorWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """
  
  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)
    
    # Instantiate and connect widgets ...
    
    self.logic = LocatorLogic(None)
    self.logic.setWidget(self)
    self.nLocators = 5
    #--------------------------------------------------
    # For debugging
    #
    # Reload and Test area
    reloadCollapsibleButton = ctk.ctkCollapsibleButton()
    reloadCollapsibleButton.text = "Reload && Test"
    self.layout.addWidget(reloadCollapsibleButton)
    reloadFormLayout = qt.QFormLayout(reloadCollapsibleButton)
    
    reloadCollapsibleButton.collapsed = True
    
    # reload button
    # (use this during development, but remove it when delivering
    #  your module to users)
    self.reloadButton = qt.QPushButton("Reload")
    self.reloadButton.toolTip = "Reload this module."
    self.reloadButton.name = "CurveMaker Reload"
    reloadFormLayout.addWidget(self.reloadButton)
    self.reloadButton.connect('clicked()', self.onReload)
    #
    #--------------------------------------------------
    
    
    #--------------------------------------------------
    # GUI components
    
    self.colorDialog = qt.QColorDialog()
    self.colorDialog.connect("colorSelected(const QColor &)", self.logic.colorSchemeChanged)
    self.layout.addWidget(self.colorDialog)
    #self.colorDialog.done()
    #
    # Registration Matrix Selection Area
    #
    selectionCollapsibleButton = ctk.ctkCollapsibleButton()
    selectionCollapsibleButton.text = "Locator ON/OFF"
    self.layout.addWidget(selectionCollapsibleButton)
    
    selectionFormLayout = qt.QFormLayout(selectionCollapsibleButton)
    
    self.connectorPort = qt.QSpinBox()
    self.connectorPort.objectName = 'PortSpinBox'
    self.connectorPort.setMaximum(64000)
    self.connectorPort.setValue(18944)
    self.connectorPort.setToolTip("Port number of the server")
    selectionFormLayout.addRow("Port: ", self.connectorPort)
    
    #
    # check box to trigger transform conversion
    #
    
    self.activeConnectionBox = qt.QCheckBox()
    self.activeConnectionBox.checked = 0
    self.activeConnectionBox.setToolTip("Activate OpenIGTLink connection")
    selectionFormLayout.addRow("Active: ", self.activeConnectionBox)
    self.activeConnectionBox.connect('toggled(bool)', self.logic.onTrackingConnectionActive)
    self.activeTrackingBox = qt.QCheckBox()
    self.activeTrackingBox.checked = 0
    self.activeTrackingBox.connect('toggled(bool)', self.logic.onStartAndStopTracking)
    selectionFormLayout.addRow("Start/Stop Tracking: ", self.activeTrackingBox)
    
    self.transformSelector = []
    self.colorSelectors = []
    self.locatorActiveCheckBox = []
    
    for i in range(self.nLocators):
      
      self.transformSelector.append(slicer.qMRMLNodeComboBox())
      selector = self.transformSelector[i]
      selector.nodeTypes = ( ("vtkMRMLLinearTransformNode"), "" )
      selector.selectNodeUponCreation = True
      selector.addEnabled = False
      selector.removeEnabled = False
      selector.noneEnabled = False
      selector.showHidden = False
      selector.showChildNodeTypes = False
      selector.setMRMLScene( slicer.mrmlScene )
      selector.setToolTip( "Establish a connection with the server" )
      
      self.colorSelectors.append(qt.QPushButton("", self.parent))
      colorSelector = self.colorSelectors[i]
      
      self.locatorActiveCheckBox.append(qt.QCheckBox())
      checkbox = self.locatorActiveCheckBox[i]
      checkbox.checked = 0
      checkbox.text = ' '
      checkbox.setToolTip("Activate locator")
      
      transformLayout = qt.QHBoxLayout()
      transformLayout.addWidget(selector)
      transformLayout.addWidget(colorSelector)
      transformLayout.addWidget(checkbox)
      selectionFormLayout.addRow("Locator #%d:" % i, transformLayout)
      
      colorSelector.connect('pressed()', lambda sender=colorSelector: self.logic.modifyColorScheme(sender))
      selector.connect('currentNodeIDChanged(const QString & )',lambda sender = selector: self.logic.reselectLocator(sender))
      checkbox.connect('toggled(bool)', self.onLocatorActive)
    #--------------------------------------------------
    # connections
    #
    
    # Add vertical spacer
    self.layout.addStretch(1)
  
  
  def cleanup(self):
    pass
  
  
  def onLocatorActive(self):
    
    removeList = {}
    for i in range(self.nLocators):
      tnode = self.transformSelector[i].currentNode()
      if self.locatorActiveCheckBox[i].checked == True:
        if tnode:
          self.transformSelector[i].setEnabled(False)
          self.logic.addLocator(tnode,i)
          mnodeID = tnode.GetAttribute('Locator')
          removeList[mnodeID] = False
        else:
          self.locatorActiveCheckBox[i].setChecked(False)
          self.transformSelector[i].setEnabled(True)
      else:
        if tnode:
          mnodeID = tnode.GetAttribute('Locator')
          if mnodeID != None and not (mnodeID in removeList):
            removeList[mnodeID] = True
            self.logic.unlinkLocator(tnode)
        self.transformSelector[i].setEnabled(True)
  
    for k, v in removeList.iteritems():
      if v:
        self.logic.removeLocator(k)

  
  def onReload(self, moduleName="Locator"):
    # Generic reload method for any scripted module.
    # ModuleWizard will subsitute correct default moduleName.
    
    globals()[moduleName] = slicer.util.reloadScriptedModule(moduleName)



#------------------------------------------------------------
#
# LocatorLogic
#
class LocatorLogic(ScriptedLoadableModuleLogic):
  
  def __init__(self, parent):
    ScriptedLoadableModuleLogic.__init__(self, parent)
    
    self.scene = slicer.mrmlScene
    self.scene.AddObserver(slicer.vtkMRMLScene.NodeRemovedEvent, self.onNodeRemovedEvent)
    self.colorList = ([0.5, 0, 0], [0, 0.5, 0], [0, 0, 0.5],[0.5, 0, 0.5],[0, 0.5, 0.5])
    self.colorMap = dict()
    self.SelectedRowNum = None
    
    @vtk.calldata_type(vtk.VTK_OBJECT)
    def updateLocator(caller, event, callerdata):
      node = callerdata
      if isinstance(node, slicer.vtkMRMLLinearTransformNode) :
        firstSelector = self.widget.transformSelector[0]
        tCollection = self.scene.GetNodesByClass("vtkMRMLLinearTransformNode")
        channelNum = tCollection.GetReferenceCount()
        setNum = self.widget.nLocators
        if channelNum < setNum:
          setNum = channelNum
        for i in range(setNum+1):
          selector = self.widget.transformSelector[i]
          selector.setCurrentNodeIndex(i)
          if self.scene.GetNodeByID(selector.currentNodeID):
            self.colorMap[self.scene.GetNodeByID(selector.currentNodeID).GetName()] = self.colorList[i]
      pass
    self.scene.AddObserver(slicer.vtkMRMLScene.NodeAddedEvent, updateLocator)
    self.widget = None
    self.cnode = slicer.vtkMRMLIGTLConnectorNode()
    self.metaDataQueryNode = vtkSlicerOpenIGTLinkIFModuleMRML.vtkMRMLIGTLQueryNode()
    self.scene.AddNode(self.cnode)
    self.scene.AddNode(self.metaDataQueryNode)
    
    self.eventTag = {}
    
    # IGTL Conenctor Node ID
    self.connectorNodeID = ''
    
    self.count = 0
  
  def setWidget(self, widget):
    self.widget = widget
  
  def onTrackingConnectionActive(self):
    if self.widget.activeConnectionBox.checked == True:
      self.cnode.SetTypeClient("localhost", self.widget.connectorPort.value)
      success = False
      attampt = 0
      while(attampt<10 and (not success) ):
        success = self.cnode.Start()
        time.sleep(0.3)
        attampt = attampt + 1
      if(not success):
        self.widget.activeConnectionBox.checked = False
    else:
      if self.cnode:
        self.cnode.Stop()
    pass

  def onStartAndStopTracking(self):
    if self.widget.activeTrackingBox.checked == True:
      self.metaDataQueryNode.SetIGTLName("TDATA")
      self.metaDataQueryNode.SetIGTLDeviceName("")
      self.metaDataQueryNode.SetQueryType(self.metaDataQueryNode.TYPE_START)
      self.metaDataQueryNode.SetQueryStatus(self.metaDataQueryNode.STATUS_PREPARED)
      self.cnode.PushQuery(self.metaDataQueryNode)
    else:
      self.metaDataQueryNode.SetIGTLName("TDATA")
      self.metaDataQueryNode.SetIGTLDeviceName("")
      self.metaDataQueryNode.SetQueryType(self.metaDataQueryNode.TYPE_STOP)
      self.metaDataQueryNode.SetQueryStatus(self.metaDataQueryNode.STATUS_PREPARED)
      self.cnode.PushQuery(self.metaDataQueryNode)
    pass


  def addLocator(self, tnode, index):
    if tnode:
      if tnode.GetAttribute('Locator') == None:
        needleModelID = self.createNeedleModelNode(tnode.GetName(),index)
        needleModel = self.scene.GetNodeByID(needleModelID)
        needleModel.SetAndObserveTransformNodeID(tnode.GetID())
        tnode.SetAttribute('Locator', needleModelID)

  def unlinkLocator(self, tnode):
    if tnode:
      print 'unlinkLocator(%s)' % tnode.GetID()
      tnode.RemoveAttribute('Locator')
  
  def removeLocator(self, mnodeID):
    if mnodeID:
      print 'removeLocator(%s)' % mnodeID
      mnode = self.scene.GetNodeByID(mnodeID)
      if mnode:
        print 'removing from the scene'
        dnodeID = mnode.GetDisplayNodeID()
        if dnodeID:
          dnode = self.scene.GetNodeByID(dnodeID)
          if dnode:
            self.scene.RemoveNode(mnode)
            self.scene.RemoveNode(dnode)
  
  
  
  def createNeedleModelNode(self, name,index):
    
    locatorModel = self.scene.CreateNodeByClass('vtkMRMLModelNode')
    
    # Cylinder represents the locator stick
    cylinder = vtk.vtkCylinderSource()
    cylinder.SetRadius(1.5)
    cylinder.SetHeight(100)
    cylinder.SetCenter(0, 0, 0)
    cylinder.Update()
    
    # Rotate cylinder
    tfilter = vtk.vtkTransformPolyDataFilter()
    trans =   vtk.vtkTransform()
    trans.RotateX(90.0)
    trans.Translate(0.0, -50.0, 0.0)
    trans.Update()
    if vtk.VTK_MAJOR_VERSION <= 5:
      tfilter.SetInput(cylinder.GetOutput())
    else:
      tfilter.SetInputConnection(cylinder.GetOutputPort())
    tfilter.SetTransform(trans)
    tfilter.Update()
    
    # Sphere represents the locator tip
    sphere = vtk.vtkSphereSource()
    sphere.SetRadius(3.0)
    sphere.SetCenter(0, 0, 0)
    sphere.Update()
    
    apd = vtk.vtkAppendPolyData()
    
    if vtk.VTK_MAJOR_VERSION <= 5:
      apd.AddInput(sphere.GetOutput())
      apd.AddInput(tfilter.GetOutput())
    else:
      apd.AddInputConnection(sphere.GetOutputPort())
      apd.AddInputConnection(tfilter.GetOutputPort())
    apd.Update()
    
    locatorModel.SetAndObservePolyData(apd.GetOutput());
    
    self.scene.AddNode(locatorModel)
    locatorModel.SetScene(self.scene);
    needleName = "Needle_%s" % name
    locatorModel.SetName(needleName)
    
    locatorDisp = locatorModel.GetDisplayNodeID()
    if locatorDisp == None:
      locatorDisp = self.scene.CreateNodeByClass('vtkMRMLModelDisplayNode')
      self.scene.AddNode(locatorDisp)
      locatorDisp.SetScene(self.scene)
      locatorModel.SetAndObserveDisplayNodeID(locatorDisp.GetID());

    color = [0, 0, 0]
    color[0] = 0.5
    color[1] = 0.5
    color[2] = 1.0
    locatorDisp.SetColor(color)
    print name
    if self.colorMap.get(name):
      locatorDisp.SetColor(self.colorMap.get(name))
      color = self.colorMap.get(name)
      colorName = "background:rgb({},{},{})".format(255*color[0], 255*color[1], 255*color[2])
      print colorName
      self.widget.colorSelectors[index].setStyleSheet(colorName)
      #qss = qt.QString("background-color: %1").arg(col.name());

    return locatorModel.GetID()

  def modifyColorScheme(self,sender):
    index = 0
    for index, colorSelector in enumerate(self.widget.colorSelectors):
      if sender == colorSelector:
        break
    self.SelectedRowNum = index
    self.widget.colorDialog.open()
    pass

  def colorSchemeChanged(self):
    if not self.SelectedRowNum==None:
      a = 0
      #fom widget get the current selected combox, from the combox get the transformation node in this combox.
      colortemp = self.widget.colorDialog.selectedColor()
      red = colortemp.red()
      green = colortemp.green()
      blue = colortemp.blue()
      colorName = "background:rgb({},{},{})".format(red, green, blue)
      self.widget.colorSelectors[self.SelectedRowNum].setStyleSheet(colorName)
      selectedColor = [red/255.0,green/255.0,blue/255.0]
      tnode = self.widget.transformSelector[self.SelectedRowNum].currentNode()
      tModelNode = self.scene.GetNodesByName("Needle_%s" % tnode.GetName()).GetItemAsObject(0)
      locatorDisp = tModelNode.GetDisplayNode()
      locatorDisp.SetColor(selectedColor)
      if tnode and self.colorMap.get(tnode.GetName()):
        self.colorMap[tnode.GetName()] = selectedColor  # conversion between QT color and slicer color needed
    pass

  def reselectLocator(self, sender):
    index = 0
    for index, transform in enumerate(self.widget.transformSelector):
      if sender == transform.currentNodeID:
        tnode = transform.currentNode()
        selectedColor = [0,0,0]
        if tnode and self.colorMap.get(tnode.GetName()):
          selectedColor = self.colorMap[tnode.GetName()]
          colorName = "background:rgb({},{},{})".format(selectedColor[0]*255, selectedColor[1]*255, selectedColor[2]*255)
          self.widget.colorSelectors[index].setStyleSheet(colorName)
    pass


  def onNodeRemovedEvent(self, caller, event, obj=None):
    delkey = ''
    if obj == None:
      for k in self.eventTag:
        node = self.scene.GetNodeByID(k)
        if node == None:
          delkey = k
          break
    
    if delkey != '':
      del self.eventTag[delkey]


