<template>
  <v-dialog
    v-model="dialog_open"
    width="500px"
  >
    <v-card>
      <v-card-title>
        Export 3D File
      </v-card-title>
      <v-container>
        <v-list>
          <v-list-item-group
            v-model="layer_selected"
          >
            <v-list-item
              v-for="layer in layer_items"
            >
              {{ layer.text }}
            </v-list-item>
          </v-list-item-group>
        </v-list>
        <v-text>Layer Options</v-text>
        <jupyter-widget :widget="layer_layout"/>
        <v-select
          v-if="method_items.length > 1"
          label="Export method"
          :items="method_items"
          v-model="method_selected"
        />
        <v-divider></v-divider>
        <v-text>File Options</v-text>
        <v-select
          label="Filetype"
          :items="filetype_items"
          v-model="filetype_selected"
        />
        <v-select
          label="Compression method"
          :items="compression_items"
          v-model="compression_selected"
        />
        <v-row>
          <v-spacer></v-spacer>
          <v-btn @click="cancel_dialog">Cancel</v-btn>
          <v-btn @click="export_viewer">Export</v-btn>
        </v-row>
      </v-container>
    </v-card>
  </v-dialog>
</template>
