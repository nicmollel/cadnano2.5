from PyQt5.QtCore import Qt
from PyQt5.QtCore import QItemSelectionModel, QItemSelection

from cadnano.enum import ItemType, PartType
from cadnano.gui.views import styles

from .cnoutlineritem import CNOutlinerItem, NAME_COL, VISIBLE_COL, COLOR_COL
from cadnano.gui.views.abstractitems.abstractpartitem import AbstractPartItem
from cadnano.gui.controllers.itemcontrollers.nucleicacidpartitemcontroller import NucleicAcidPartItemController
from .oligoitem import OligoItem
from .virtualhelixitem import VirtualHelixItem

class NucleicAcidPartItem(CNOutlinerItem, AbstractPartItem):
    FILTER_NAME = "part"
    def __init__(self, model_part, parent):
        super(NucleicAcidPartItem, self).__init__(model_part, parent)
        self._controller = NucleicAcidPartItemController(self, model_part)
        self.setExpanded(True)

        # properties
        temp_color = model_part.getColor()
        # outlinerview takes responsibility of overriding default part color
        if temp_color == "#000000":
            index = len(model_part.document().children()) - 1
            new_color = styles.PARTCOLORS[index % len(styles.PARTCOLORS)]
            model_part.setProperty('color', new_color)

        # item groups
        self._root_items = {}
        self._root_items['VHelixList'] = self.createRootPartItem('Virtual Helices', self)
        self._root_items['OligoList'] = self.createRootPartItem('Oligos', self)
        # self._root_items['Modifications'] = self._createRootItem('Modifications', self)
    # end def

    ### PRIVATE SUPPORT METHODS ###

    ### PUBLIC SUPPORT METHODS ###
    def rootItems(self):
        return self._root_items
    # end def

    def part(self):
        return self._cn_model
    # end def

    def itemType(self):
        return ItemType.NUCLEICACID
    # end def

    ### SLOTS ###
    def partRemovedSlot(self, sender):
        self._controller.disconnectSignals()
        self._cn_model = None
        self._controller = None
    # end def

    def partOligoAddedSlot(self, model_part, model_oligo):
        m_o = model_oligo
        m_o.oligoRemovedSignal.connect(self.partOligoRemovedSlot)
        o_i = OligoItem(m_o, self._root_items['OligoList'])
        self._oligo_item_hash[m_o] = o_i
    # end def

    def partOligoRemovedSlot(self, model_part, model_oligo):
        m_o = model_oligo
        m_o.oligoRemovedSignal.disconnect(self.partOligoRemovedSlot)
        o_i = self._oligo_item_hash[m_o]
        o_i.parent().removeChild(o_i)
        del self._oligo_item_hash[m_o]
    # end def

    def partVirtualHelixAddedSlot(self, model_part, id_num):
        tw = self.treeWidget()
        tw.is_child_adding += 1
        vh_i = VirtualHelixItem(id_num, self._root_items['VHelixList'])
        self._virtual_helix_item_hash[id_num] = vh_i
        tw.is_child_adding -= 1

    def partVirtualHelixRemovedSlot(self, model_part, id_num):
        vh_i = self._virtual_helix_item_hash.get(id_num)
        # in case a VirtualHelixItem Object is cleaned up before this happends
        if vh_i is not None:
            del self._virtual_helix_item_hash[id_num]
            vh_i.parent().removeChild(vh_i)
    # end def

    def partPropertyChangedSlot(self, model_part, property_key, new_value):
        if self._cn_model == model_part:
            self.setValue(property_key, new_value)
    # end def

    def partSelectedChangedSlot(self, model_part, is_selected):
        # print("part", is_selected)
        self.setSelected(is_selected)
    # end def

    def partVirtualHelixPropertyChangedSlot(self, sender, id_num, keys, values):
        if self._cn_model == sender:
            vh_i = self._virtual_helix_item_hash[id_num]
            for key, val in zip(keys, values):
                if key in CNOutlinerItem.PROPERTIES:
                    vh_i.setValue(key, val)
    # end def

    def partVirtualHelicesSelectedSlot(self, sender, vh_set, is_adding):
        """ is_adding (bool): adding (True) virtual helices to a selection
        or removing (False)
        """
        vhi_hash = self._virtual_helix_item_hash
        tw = self.treeWidget()
        model = tw.model()
        selection_model = tw.selectionModel()
        top_idx = tw.indexOfTopLevelItem(self)
        top_midx = model.index(top_idx, 0)
        vh_list = self._root_items['VHelixList']
        root_midx = model.index(self.indexOfChild(vh_list), 0, top_midx)
        if is_adding:
            flag = QItemSelectionModel.Select
            for id_num in vh_set:
                vhi = vhi_hash.get(id_num)
                # selecting a selected item will deselect it, so check
                if not vhi.isSelected():
                    idx = vh_list.indexOfChild(vhi)
                    selection_model.select(model.index(idx, 0, root_midx), flag)
        else:
            flag = QItemSelectionModel.Deselect
            for id_num in vh_set:
                vhi = vhi_hash.get(id_num)
                # deselecting a deselected item will select it, so check
                if vhi.isSelected():
                    idx = vh_list.indexOfChild(vhi)
                    selection_model.select(model.index(idx, 0, root_midx), flag)
    # end def

    def partVirtualHelicesReorderedSlot(self, sender, ordered_id_list, check_batch):
        """docstring for partVirtualHelicesReorderedSlot"""
        vhi_dict = self._virtual_helix_item_hash
        new_list = [vhi_dict[id_num] for id_num in ordered_id_list]
        root_vhi = self._root_items['VHelixList']
        root_vhi.takeChildren()
        for vhi in new_list:
            root_vhi.addChild(vhi)
    # end def
# end class
