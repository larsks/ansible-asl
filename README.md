This repository contains:

- An example `callback_plugin` for ansible that logs tasks in JSON
  format to a file named `ansible_log.json` in the current directory.

- A script called `log2html.py` (and a corresponding template) that
  generates an HTML view of this log.  Run it like this:

        python log2html.py < ansible_log.json > doc.html

## About the HTML output

The HTML output contains a table with one row/task.  Clicking on a row
will show/hide the tasks results.  Text in each row is colored
according to the task status:

- `ok` is colored green
- `failed` is colored red, unless `ignore_errors` is `true` in which
  case it is orange,
- `skipped` is blue

## Example

There is a simple example included in this repository.  Run it like
this:

    cd example
    ansible-playbook playbook.yml
    cd ..
    python log2html.py < example/ansible_log.json > doc.html

Then open the resulting `doc.html` in your browser.
