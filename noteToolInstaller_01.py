"""
Maya Notes Plugin Auto-Installer
Run this in Maya's Script Editor (Python tab)
"""

import maya.cmds as cmds
import os

def install_notes_plugin():
    plugin_code = """\"\"\"
Maya Notes Plugin
Embeds notes into Maya files using a custom node with text editor and viewport display
\"\"\"

def maya_useNewAPI():
    \"\"\"Tell Maya to use the Maya Python API 2.0\"\"\"
    pass

import maya.api.OpenMaya as om2
import maya.api.OpenMayaUI as omui2
import maya.api.OpenMayaRender as omr2
import maya.cmds as cmds
from PySide2 import QtWidgets, QtCore, QtGui
from maya import OpenMayaUI as OpenMayaUI1  # Old API for MQtUtil

# Plugin information
kPluginNodeName = "notesNode"
kPluginNodeId = om2.MTypeId(0x00123456)  # Change this to a unique ID

class NotesNode(omui2.MPxLocatorNode):
    \"\"\"Custom locator node that stores text notes\"\"\"
    
    # Attributes
    noteText = None
    noteTitle = None
    displayInViewport = None
    fontSize = None
    textColor = None
    
    def __init__(self):
        omui2.MPxLocatorNode.__init__(self)
    
    @staticmethod
    def creator():
        return NotesNode()
    
    @staticmethod
    def initialize():
        # Create string attribute for note text
        tAttr = om2.MFnTypedAttribute()
        NotesNode.noteText = tAttr.create("noteText", "nt", om2.MFnData.kString)
        tAttr.writable = True
        tAttr.storable = True
        
        # Create string attribute for note title
        NotesNode.noteTitle = tAttr.create("noteTitle", "ttl", om2.MFnData.kString)
        tAttr.writable = True
        tAttr.storable = True
        
        # Create bool attribute for viewport display
        nAttr = om2.MFnNumericAttribute()
        NotesNode.displayInViewport = nAttr.create("displayInViewport", "div", om2.MFnNumericData.kBoolean, True)
        nAttr.writable = True
        nAttr.storable = True
        
        # Create int attribute for font size
        NotesNode.fontSize = nAttr.create("fontSize", "fs", om2.MFnNumericData.kInt, 12)
        nAttr.writable = True
        nAttr.storable = True
        nAttr.setMin(8)
        nAttr.setMax(72)
        
        # Create color attribute
        NotesNode.textColor = nAttr.createColor("textColor", "tc")
        nAttr.writable = True
        nAttr.storable = True
        nAttr.default = (1.0, 1.0, 0.0)  # Yellow by default
        
        # Add attributes
        NotesNode.addAttribute(NotesNode.noteText)
        NotesNode.addAttribute(NotesNode.noteTitle)
        NotesNode.addAttribute(NotesNode.displayInViewport)
        NotesNode.addAttribute(NotesNode.fontSize)
        NotesNode.addAttribute(NotesNode.textColor)
    
    def draw(self, view, path, style, status):
        \"\"\"Legacy viewport drawing (VP1)\"\"\"
        pass


class NotesNodeDrawOverride(omr2.MPxDrawOverride):
    \"\"\"Viewport 2.0 draw override for displaying notes in viewport\"\"\"
    
    @staticmethod
    def creator(obj):
        return NotesNodeDrawOverride(obj)
    
    def __init__(self, obj):
        omr2.MPxDrawOverride.__init__(self, obj, None, False)
    
    def supportedDrawAPIs(self):
        return omr2.MRenderer.kAllDevices
    
    def prepareForDraw(self, objPath, cameraPath, frameContext, oldData):
        \"\"\"Prepare data for drawing\"\"\"
        data = {}
        
        try:
            node = objPath.node()
            plug = om2.MPlug(node, NotesNode.displayInViewport)
            data['display'] = plug.asBool()
            
            if data['display']:
                plug = om2.MPlug(node, NotesNode.noteText)
                data['text'] = plug.asString()
                
                plug = om2.MPlug(node, NotesNode.noteTitle)
                data['title'] = plug.asString()
                
                plug = om2.MPlug(node, NotesNode.fontSize)
                data['fontSize'] = plug.asInt()
                
                plug = om2.MPlug(node, NotesNode.textColor)
                data['color'] = (plug.child(0).asFloat(), plug.child(1).asFloat(), plug.child(2).asFloat())
        except:
            # If anything fails, just don't draw
            data['display'] = False
        
        return data
    
    def hasUIDrawables(self):
        return True
    
    def addUIDrawables(self, objPath, drawManager, frameContext, data):
        \"\"\"Draw text in viewport\"\"\"
        if not data or not data.get('display'):
            return
        
        drawManager.beginDrawable()
        
        # Set color
        color = data.get('color', (1, 1, 0))
        drawManager.setColor(om2.MColor(color))
        
        # Set font size
        fontSize = data.get('fontSize', 12)
        drawManager.setFontSize(fontSize)
        
        # Draw title and text
        title = data.get('title', '')
        text = data.get('text', '')
        
        position = om2.MPoint(0, 0, 0)
        
        if title:
            drawManager.text(position, title, omr2.MUIDrawManager.kCenter)
            position.y -= 0.5
        
        if text:
            lines = text.split('\\n')[:5]  # Limit to 5 lines in viewport
            for line in lines:
                drawManager.text(position, line[:50], omr2.MUIDrawManager.kCenter)  # Limit line length
                position.y -= 0.3
        
        drawManager.endDrawable()


class NotesEditorWindow(QtWidgets.QDialog):
    \"\"\"Text editor window for creating/editing notes\"\"\"
    
    def __init__(self, parent=None):
        super(NotesEditorWindow, self).__init__(parent)
        self.setWindowTitle("Notes Editor")
        self.setMinimumSize(400, 500)
        self.currentNode = None
        
        # Make window stay on top
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        
        self.setupUI()
        self.loadLastNote()
    
    def setupUI(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        # Node selection
        nodeLayout = QtWidgets.QHBoxLayout()
        nodeLayout.addWidget(QtWidgets.QLabel("Note Node:"))
        self.nodeCombo = QtWidgets.QComboBox()
        self.nodeCombo.currentIndexChanged.connect(self.loadNote)
        nodeLayout.addWidget(self.nodeCombo)
        
        refreshBtn = QtWidgets.QPushButton("Refresh")
        refreshBtn.clicked.connect(self.refreshNodes)
        nodeLayout.addWidget(refreshBtn)
        
        createBtn = QtWidgets.QPushButton("Create New")
        createBtn.clicked.connect(self.createNewNote)
        nodeLayout.addWidget(createBtn)
        
        layout.addLayout(nodeLayout)
        
        # Title
        titleLayout = QtWidgets.QHBoxLayout()
        titleLayout.addWidget(QtWidgets.QLabel("Title:"))
        self.titleEdit = QtWidgets.QLineEdit()
        titleLayout.addWidget(self.titleEdit)
        layout.addLayout(titleLayout)
        
        # Text editor
        layout.addWidget(QtWidgets.QLabel("Note Content:"))
        self.textEdit = QtWidgets.QPlainTextEdit()
        self.textEdit.setFont(QtGui.QFont("Courier", 10))
        layout.addWidget(self.textEdit)
        
        # Options
        optionsLayout = QtWidgets.QHBoxLayout()
        
        self.displayCheck = QtWidgets.QCheckBox("Display in Viewport")
        self.displayCheck.setChecked(True)
        optionsLayout.addWidget(self.displayCheck)
        
        optionsLayout.addWidget(QtWidgets.QLabel("Font Size:"))
        self.fontSizeSpin = QtWidgets.QSpinBox()
        self.fontSizeSpin.setRange(8, 72)
        self.fontSizeSpin.setValue(12)
        optionsLayout.addWidget(self.fontSizeSpin)
        
        optionsLayout.addStretch()
        layout.addLayout(optionsLayout)
        
        # Buttons
        buttonLayout = QtWidgets.QHBoxLayout()
        saveBtn = QtWidgets.QPushButton("Save")
        saveBtn.clicked.connect(self.saveNote)
        buttonLayout.addWidget(saveBtn)
        
        deleteBtn = QtWidgets.QPushButton("Delete Node")
        deleteBtn.clicked.connect(self.deleteNote)
        buttonLayout.addWidget(deleteBtn)
        
        closeBtn = QtWidgets.QPushButton("Close")
        closeBtn.clicked.connect(self.close)
        buttonLayout.addWidget(closeBtn)
        
        layout.addLayout(buttonLayout)
        
        self.refreshNodes()
    
    def refreshNodes(self):
        \"\"\"Refresh the list of notes nodes\"\"\"
        self.nodeCombo.clear()
        nodes = cmds.ls(type=kPluginNodeName)
        if nodes:
            self.nodeCombo.addItems(nodes)
            self.loadNote()
    
    def loadLastNote(self):
        \"\"\"Load the last used note or create one if none exist\"\"\"
        nodes = cmds.ls(type=kPluginNodeName)
        if nodes:
            # Load the first note found
            self.nodeCombo.addItems(nodes)
            self.loadNote()
        else:
            # No notes exist, create one
            self.createNewNote()
    
    def createNewNote(self):
        \"\"\"Create a new notes node\"\"\"
        try:
            # Create or get the NOTES group
            notes_group = "NOTES"
            if not cmds.objExists(notes_group):
                notes_group = cmds.group(empty=True, name=notes_group)
                # Lock transform attributes
                for attr in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz']:
                    cmds.setAttr(f"{notes_group}.{attr}", lock=True)
            
            # Create node with transform parent
            transform = cmds.createNode("transform", name="note_NewNote")
            node = cmds.createNode(kPluginNodeName, parent=transform, skipSelect=True)
            
            # Parent to NOTES group
            cmds.parent(transform, notes_group)
            
            if cmds.objExists(node):
                cmds.setAttr(node + ".noteTitle", "New Note", type="string")
                self.refreshNodes()
                # Select the new node in combo
                index = self.nodeCombo.findText(node)
                if index >= 0:
                    self.nodeCombo.setCurrentIndex(index)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to create note: {str(e)}")
    
    def loadNote(self):
        \"\"\"Load note from selected node\"\"\"
        nodeName = self.nodeCombo.currentText()
        if not nodeName or not cmds.objExists(nodeName):
            return
        
        self.currentNode = nodeName
        
        # Load attributes
        title = cmds.getAttr(nodeName + ".noteTitle") or ""
        text = cmds.getAttr(nodeName + ".noteText") or ""
        display = cmds.getAttr(nodeName + ".displayInViewport")
        fontSize = cmds.getAttr(nodeName + ".fontSize")
        
        self.titleEdit.setText(title)
        self.textEdit.setPlainText(text)
        self.displayCheck.setChecked(display)
        self.fontSizeSpin.setValue(fontSize)
    
    def saveNote(self):
        \"\"\"Save note to current node\"\"\"
        if not self.currentNode or not cmds.objExists(self.currentNode):
            QtWidgets.QMessageBox.warning(self, "Error", "No valid node selected")
            return
        
        title = self.titleEdit.text()
        text = self.textEdit.toPlainText()
        display = self.displayCheck.isChecked()
        fontSize = self.fontSizeSpin.value()
        
        cmds.setAttr(self.currentNode + ".noteTitle", title, type="string")
        cmds.setAttr(self.currentNode + ".noteText", text, type="string")
        cmds.setAttr(self.currentNode + ".displayInViewport", display)
        cmds.setAttr(self.currentNode + ".fontSize", fontSize)
        
        # Rename the transform node based on title
        transform = cmds.listRelatives(self.currentNode, parent=True)
        if transform:
            safe_title = title.replace(" ", "_").replace("/", "_").replace("\\\\", "_")
            if not safe_title:
                safe_title = "note"
            new_name = f"note_{safe_title}"
            try:
                cmds.rename(transform[0], new_name)
            except:
                pass  # If rename fails, just continue
        
        cmds.refresh()
        QtWidgets.QMessageBox.information(self, "Success", "Note saved successfully!")
    
    def deleteNote(self):
        \"\"\"Delete the current notes node\"\"\"
        if not self.currentNode:
            return
        
        reply = QtWidgets.QMessageBox.question(
            self, "Confirm Delete",
            f"Delete note node '{self.currentNode}'?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            if cmds.objExists(self.currentNode):
                cmds.delete(self.currentNode)
            self.refreshNodes()


# Global window instance
notesWindow = None

def showNotesEditor():
    \"\"\"Show the notes editor window\"\"\"
    global notesWindow
    
    if notesWindow is None:
        # Get Maya main window using old API
        mayaMainWindowPtr = OpenMayaUI1.MQtUtil.mainWindow()
        if mayaMainWindowPtr:
            mayaMainWindow = QtWidgets.QWidget.find(int(mayaMainWindowPtr))
        else:
            mayaMainWindow = None
        notesWindow = NotesEditorWindow(mayaMainWindow)
        
        # Position window to the right side of Maya window
        if mayaMainWindow:
            mayaGeo = mayaMainWindow.geometry()
            windowWidth = 400
            notesWindow.setGeometry(
                mayaGeo.right() - windowWidth - 10,  # 10px from right edge
                mayaGeo.top() + 100,  # 100px from top
                windowWidth,
                mayaGeo.height() - 200  # Leave some space at bottom
            )
    
    notesWindow.show()
    notesWindow.raise_()
    notesWindow.activateWindow()


def createNoteFromMenu():
    \"\"\"Create a note from the menu\"\"\"
    # Create or get the NOTES group
    notes_group = "NOTES"
    if not cmds.objExists(notes_group):
        notes_group = cmds.group(empty=True, name=notes_group)
        # Lock transform attributes
        for attr in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz']:
            cmds.setAttr(f"{notes_group}.{attr}", lock=True)
    
    # Create node with transform parent
    transform = cmds.createNode("transform", name="note_NewNote")
    node = cmds.createNode(kPluginNodeName, parent=transform, skipSelect=True)
    
    # Parent to NOTES group
    cmds.parent(transform, notes_group)
    
    # Set default title
    cmds.setAttr(node + ".noteTitle", "New Note", type="string")
    om2.MGlobal.displayInfo(f"Created note: {node}")


# Plugin initialization
def initializePlugin(obj):
    plugin = om2.MFnPlugin(obj, "Notes Plugin", "1.0", "Any")
    
    try:
        plugin.registerNode(
            kPluginNodeName,
            kPluginNodeId,
            NotesNode.creator,
            NotesNode.initialize,
            om2.MPxNode.kLocatorNode,
            None
        )
    except:
        om2.MGlobal.displayError("Failed to register node: " + kPluginNodeName)
        raise
    
    try:
        omr2.MDrawRegistry.registerDrawOverrideCreator(
            "drawdb/geometry/notesNode",
            kPluginNodeName,
            NotesNodeDrawOverride.creator
        )
    except:
        om2.MGlobal.displayError("Failed to register draw override")
        raise
    
    # Add menu item
    if cmds.menu("NotesMenu", exists=True):
        cmds.deleteUI("NotesMenu")
    
    cmds.menu("NotesMenu", label="Notes", parent="MayaWindow", tearOff=True)
    cmds.menuItem(label="Open Notes Editor", command=lambda *args: showNotesEditor())
    cmds.menuItem(label="Create Note", command=lambda *args: createNoteFromMenu())
    
    # Auto-open notes editor on startup
    cmds.evalDeferred(showNotesEditor)
    
    om2.MGlobal.displayInfo("Notes Plugin loaded successfully")


def uninitializePlugin(obj):
    plugin = om2.MFnPlugin(obj)
    
    try:
        omr2.MDrawRegistry.deregisterDrawOverrideCreator(
            "drawdb/geometry/notesNode",
            kPluginNodeName
        )
    except:
        om2.MGlobal.displayError("Failed to deregister draw override")
    
    try:
        plugin.deregisterNode(kPluginNodeId)
    except:
        om2.MGlobal.displayError("Failed to deregister node: " + kPluginNodeName)
        raise
    
    # Remove menu
    if cmds.menu("NotesMenu", exists=True):
        cmds.deleteUI("NotesMenu")
    
    om2.MGlobal.displayInfo("Notes Plugin unloaded")
"""
    
    # Get Maya plug-ins directory
    plugin_dir = cmds.internalVar(userAppDir=True) + "plug-ins/"
    
    # Create plug-ins directory if it doesn't exist
    if not os.path.exists(plugin_dir):
        os.makedirs(plugin_dir)
    
    plugin_path = plugin_dir + "notesPlugin.py"
    
    try:
        # Write the plugin file
        with open(plugin_path, 'w') as f:
            f.write(plugin_code)
        
        print("// Plugin installed to: " + plugin_path)
        
        # Unload if already loaded
        if cmds.pluginInfo("notesPlugin", query=True, loaded=True):
            cmds.unloadPlugin("notesPlugin")
            print("// Unloaded existing plugin")
        
        # Load the plugin
        cmds.loadPlugin(plugin_path)
        print("// Plugin loaded successfully!")
        
        # Set to auto-load (try with full path if plugin name fails)
        try:
            cmds.pluginInfo("notesPlugin", edit=True, autoload=True)
            print("// Plugin set to auto-load on startup")
        except:
            try:
                cmds.pluginInfo(plugin_path, edit=True, autoload=True)
                print("// Plugin set to auto-load on startup")
            except:
                print("// Warning: Could not set auto-load, but plugin is installed and loaded")
        
        cmds.confirmDialog(
            title="Installation Complete",
            message="Notes Plugin installed successfully!\\n\\n" +
                    "Location: " + plugin_path + "\\n\\n" +
                    "The plugin is now loaded and will auto-load on Maya startup.\\n" +
                    "Check the 'Notes' menu in the main menu bar!",
            button="OK"
        )
        
    except Exception as e:
        cmds.error("Failed to install plugin: " + str(e))

# Run the installer
install_notes_plugin()