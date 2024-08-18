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
        <!--
        <v-list
          :items="layer_items"
          v-model:selected="dialog_state.layer"
        ></v-list>
        -->
        <v-text>Layer Options</v-text>
        <jupyter-widget :widget="layer_layout"/>
        <v-select
          v-if="method_items.length > 1"
          label="Export method"
          :items="method_items"
          v-model="method_selected"
        />
        <!--
        <v-divider></v-divider>
        <v-text>File Options</v-text>
        <v-select
          label="Filetype"
          :items="filetype_items"
          v-model="state.filetype"
        />
        <v-select
          v-if="['glB', 'glTF'].includes(state.filetype)"
          label="Compression method"
          :items="compression_items"
          v-model="state.compression"
        />
        <v-row>
          <v-spacer></v-spacer>
          <v-btn @click="cancel">Cancel</v-btn>
          <v-btn @click="export">Export</v-btn>
        </v-row>
    -->
      </v-container>
    </v-card>
  </v-dialog>
</template>
