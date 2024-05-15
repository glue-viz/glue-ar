const shell = require("shelljs");

console.log("Inside glue-ar-export");

shell.mkdir("-p", "../glue_ar/js");
shell.cp("-r", "node_modules", "../glue_ar/js/");

