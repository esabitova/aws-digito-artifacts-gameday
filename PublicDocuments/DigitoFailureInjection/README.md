# Digito Failure Injection Public Documents
Digito Failure Injection Public Documents provide SSM documents for Digito failure injections.

# Running Integration Tests
Public SSM document team maintains the process for running tests at https://quip-amazon.com/1bjBAZ3I7UQx/Documents-Testing-Framework-Guide

# Work Around for Running Integration Tests
After modifying a document, the above process will need to build two brazil workspaces, which takes a while. The following is a workaround for fast development:
* Copy the whole TestingFramework directory from https://code.amazon.com/packages/SsmDocument/trees/mainline/--/PublicDocuments/TestingFramework to a local directory
* Add TestingFramework to your PYTHONPATH
* Modify method get_credentail_pair() to directly return AWS credential pair in the form of ('publicAccessKey','privateAccessKey'). The function lives in service_client.py under TestingFramework
* Run tests, e.g. python test_document.py
