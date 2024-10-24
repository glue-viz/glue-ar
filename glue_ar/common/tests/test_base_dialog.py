from random import random, seed
from typing import Any

from echo import CallbackProperty
from glue.core import Application, Data
from glue.core.link_helpers import LinkSame
from glue.core.state_objects import State
from numpy import arange, ones


class DummyState(State):
    cb_int = CallbackProperty(0)
    cb_float = CallbackProperty(1.7)
    cb_bool = CallbackProperty(False)


class BaseExportDialogTest:

    app: Application
    dialog: Any

    def _setup_data(self):
        seed(102)
        self.volume_data = Data(
                label='Volume Data',
                x=arange(24).reshape((2, 3, 4)),
                y=ones((2, 3, 4)),
                z=arange(100, 124).reshape((2, 3, 4)))
        self.app.data_collection.append(self.volume_data)

        scatter_size = 50
        self.scatter_data = Data(x=[random() for _ in range(scatter_size)],
                                 y=[random() for _ in range(scatter_size)],
                                 z=[random() for _ in range(scatter_size)],
                                 label="Scatter Data")
        self.app.data_collection.append(self.scatter_data)

        # Link pixel axes to scatter
        for i, c in enumerate(('x', 'y', 'z')):
            ri = 2 - i
            c1 = self.volume_data.id[f"Pixel Axis {ri} [{c}]"]
            c2 = self.scatter_data.id[c]
            self.app.data_collection.add_link(LinkSame(c1, c2))

    def test_default_state(self):
        state = self.dialog.state
        assert state.filetype == "glB"
        assert state.compression == "None"
        assert state.layer == "Volume Data"
        assert state.method in {"Isosurface", "Voxel"}

        assert state.filetype_helper.choices == ['glB', 'glTF', 'USDZ', 'USDC', 'USDA', 'STL']
        assert state.compression_helper.choices == ['None', 'Draco', 'Meshoptimizer']
        assert state.layer_helper.choices == ["Volume Data", "Scatter Data"]
        assert set(state.method_helper.choices) == {"Isosurface", "Voxel"}

    def test_default_dictionary(self):
        state_dict = self.dialog.state_dictionary
        assert len(state_dict) == 2
        assert set(state_dict.keys()) == {"Volume Data", "Scatter Data"}

    def test_layer_change_state(self):
        state = self.dialog.state

        state.layer = "Scatter Data"
        assert state.method_helper.choices == ["Scatter"]
        assert state.method == "Scatter"

        state.layer = "Volume Data"
        assert set(state.method_helper.choices) == {"Isosurface", "Voxel"}
        assert state.method in {"Isosurface", "Voxel"}

        state.layer = "Scatter Data"
        assert state.method_helper.choices == ["Scatter"]
        assert state.method == "Scatter"

    def test_method_settings_persistence(self):
        state = self.dialog.state

        state.layer = "Volume Data"
        state.method = "Voxel"
        method, layer_export_state = self.dialog.state_dictionary["Volume Data"]
        assert method == "Voxel"
        layer_export_state.opacity_cutoff = 0.5

        state.method = "Isosurface"
        method, layer_export_state = self.dialog.state_dictionary["Volume Data"]
        layer_export_state.isosurface_count = 25

        state.method = "Voxel"
        method, layer_export_state = self.dialog.state_dictionary["Volume Data"]
        assert method == "Voxel"
        assert layer_export_state.opacity_cutoff == 0.5

        state.layer = "Scatter Data"

        state.layer = "Volume Data"
        state.method = "Voxel"
        method, layer_export_state = self.dialog.state_dictionary["Volume Data"]
        assert method == "Voxel"
        assert layer_export_state.opacity_cutoff == 0.5

        state.method = "Isosurface"
        method, layer_export_state = self.dialog.state_dictionary["Volume Data"]
        assert method == "Isosurface"
        assert layer_export_state.isosurface_count == 25
