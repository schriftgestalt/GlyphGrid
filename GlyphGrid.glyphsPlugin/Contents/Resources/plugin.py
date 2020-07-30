# encoding: utf-8

###########################################################################################################
#
#
#	General Plugin
#
#	Read the docs:
#	https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates/General%20Plugin
#
#
###########################################################################################################

from __future__ import division, print_function, unicode_literals
import objc
from GlyphsApp import *
from GlyphsApp.plugins import *
from AppKit import NSUserDefaultsController, NSPredicate, NSCompoundPredicate

class GlyphGrid(GeneralPlugin):

	window = objc.IBOutlet()
	glyphView = objc.IBOutlet()
	glyphsArray = objc.IBOutlet()
	searchField = objc.IBOutlet()

	@objc.python_method
	def settings(self):
		self.isUpdating = False
		self.font = None
		self._masterIndex = 0
		self.name = Glyphs.localize({
			'en': 'Glyph Grid',
			'de': 'Glyph Raster',
		})
		self.loadNib("GlyphPanel", __file__)

	@objc.python_method
	def start(self):
		newMenuItem = NSMenuItem(self.name, self.showWindow_)
		Glyphs.menu[EDIT_MENU].append(newMenuItem)
		
		NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(self, self.slowUpdate_, "GSUpdateInterface", None)
		NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(self, self.slowUpdate_, "GSDocumentCloseNotification", None)
		self.glyphView.bind_toObject_withKeyPath_options_("content", self.glyphsArray, "arrangedObjects", 0)
		self.glyphView.bind_toObject_withKeyPath_options_("selectionIndexes", self.glyphsArray, "selectionIndexes", 0)

		self.glyphView.setIconHeight_(72)

		Defaults = NSUserDefaultsController.sharedUserDefaultsController()
		Defaults.addObserver_forKeyPath_options_context_(self, "values.GlyphGridSelectedMode", 0, None)
		Defaults.addObserver_forKeyPath_options_context_(self, "values.GlyphGridSearch", 0, None)

		if Glyphs.boolDefaults["GlyphGridOpen"]:
			self.openWindow()

	def showWindow_(self, sender):
		"""Do something like show a window """
		print("show Window")
		self.openWindow()

	def __del__(self):
		NSNotificationCenter.defaultCenter.removeObserver_(self)
		self.glyphView.unbind_("content")
		self.glyphView.unbind_("selectionIndexes")
		Defaults = NSUserDefaultsController.sharedUserDefaultsController()
		Defaults.removeObserver_forKeyPath_(self, "values.GlyphGridSelectedMode")
		Defaults.removeObserver_forKeyPath_(self, "values.GlyphGridSearch")

	def observeValueForKeyPath_ofObject_change_context_(self, keyPath, aObject, change, context):
		if self.isUpdating:
			return
		
		if keyPath == "font.glyphs":
			self.isUpdating = True
			self.font = None
			self.update()
			self.isUpdating = False
		elif keyPath == "values.GlyphGridSelectedMode" or keyPath == "values.GlyphGridSearch":
			self.updateFilter_(self)

	def openWindow(self):
		print(self.window, self.window.frame())
		try:
			self.update()
			self.updateFilter_(self)
			self.window.makeKeyAndOrderFront_(self)
			self.window.center()
			Glyphs.defaults["GlyphGridOpen"] = True
		except:
			import traceback
			print(traceback.format_exc())

	def windowWillClose_(self, notification):
		Glyphs.defaults["GlyphGridOpen"] = False

	def doubleClickedCollectionView_(self, collectionView):
		layer = self.font.parent.windowController().activeEditViewController().activeLayer()

		if self.glyphsArray.selectedObjects().count() > 4:
			alert = NSAlert.new()
			alert.setMessageText_("Do you really want to add %d components?" % self.glyphsArray.selectedObjects().count())
			alert.addButtonWithTitle_("Add")
			alert.addButtonWithTitle_("Cancel")
			response = alert.runModal()
			if response == NSAlertSecondButtonReturn:
				return
		XOffset = 0
		for glyph in self.glyphsArray.selectedObjects():
			component = GSComponent(glyph.name, NSMakePoint(XOffset, 0))
			layer.components.append(component)
			componentLayer = component.componentLayer
			XOffset += max(30, componentLayer.width)

	def slowUpdate_(self, sender):
		self.performSelector_withObject_afterDelay_(self.update, None, 0)

	def update_(self, notification):
		self.update()
	
	def update(self):
		newFont = Glyphs.font
		newMasterIndex = self.getCurrentMasterIndex()
		if newFont != self.font or self._masterIndex != newMasterIndex:
			if self._masterIndex != newMasterIndex:
				self.glyphView.reflow()

			if newFont != self.font:
				self.glyphsArray.setContent_(list(newFont.glyphs))

			self.font = newFont
			self._masterIndex = newMasterIndex
			self.updateFilter_(self)

	def updateFilter_(self, sender):
		filters = [];
		defaults = NSUserDefaults.standardUserDefaults()
		mode = defaults.integerForKey_("GlyphGridSelectedMode")
		if mode == 1:
			filters.append(NSPredicate.predicateWithFormat_("isSmartGlyph == 1"))
		elif mode == 2:
			filters.append(NSPredicate.predicateWithFormat_("isCorner == 1"))
		
		searchString = self.searchField.stringValue()
		if len(searchString) > 0:
			searchFilter = NSPredicate.predicateWithFormat_("name contains[cd] %@", searchString)
			if searchFilter:
				filters.append(searchFilter)

		if len(filters) > 0:
			try:
				self.glyphsArray.setFilterPredicate_(NSCompoundPredicate.andPredicateWithSubpredicates_(filters))
			except:
				import traceback
				print(traceback.format_exc())
		elif self.glyphsArray.filterPredicate() is not None:
			self.glyphsArray.setFilterPredicate_(None)

	def reusableViewControllerForCollectionView_(self, iconView):
		return NSClassFromString("GSCollectionViewItemController").new()

	def collectionView_willShowViewController_forItem_(self, iconView, viewController, anItem):
		if viewController.representedObject() != anItem:
			viewController.setRepresentedObject_(anItem)
			viewController.view().setNeedsDisplay_(True)

	def collectionViewShouldDrawSelections_(self, iconView):
		return True

	def collectionView_updateViewControllerAsSelected_forItem_(self, iconView, viewController, item):
		viewController.view().setSelected_(True)

	def collectionView_updateViewControllerAsDeselected_forItem_(self, iconView, viewController, item):
		viewController.view().setSelected_(False)

	def getCurrentMasterIndex(self):
		try:
			return Glyphs.font.masterIndex
		except:
			return 0

	@objc.python_method
	def __file__(self):
		"""Please leave this method unchanged"""
		return __file__
	
	
	