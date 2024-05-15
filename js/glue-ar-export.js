const shell = require("shelljs");

shell.mkdir("-p", "../glue_ar/js");
shell.cp("-r", "node_modules", "../glue_ar/js/");

