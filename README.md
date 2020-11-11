# Digito Failure Injection Documents
This package provides SSM documents for injecting failures in different aws resources.

# Publishing Documents
* Use below command to publish all documents in us-west-2 region to your account. Needs python3.6 or later
python3 publisher/publish_documents.py --region us-west-2

* Use below command to publish limited number of documents in different file. We will provide this file during
  recommendations for relevant test documents
python3 publisher/publish_documents.py --region us-west-2 --file-name ec2-manifest --log-level INFO

* Setting up automated publish to account
  TBD. Setup CodeBuild process for publishing documents automatically to account when there is a change

* What does publisher do?
** Gets list of documents to publish based on manifest file.
** Upload scripts zip file to S3
** Append documents that need attachment to include the checksum, size and name of scripts zip file
** Check documents which have changed and create or update document as needed to publish

# Contributing to this package
# Package Organization
* documents/test -- This folder contains ssm automation documents which can be used directly in Digito to run test. Each service
  will have a separate folder for its test documents.
* documents/util -- This folder contains ssm documents(both command and automation) and python scripts used by ssm documents which are helpers
  for test SSM documents. These documents do not run test on their own.
* documents/util/scripts -- This folder contains python scripts used by ssm documents to setup or run tests.
* publisher -- This folder contains python scripts to validate and publish ssm documents required in account.

# Adding new document
* Test Document -- Test documents need to be automation document only. Add test documents to documents/test/<service> folder.
  Each folder would contain the Design, Documents and Test folder. Design would specify the input, output and permission needed
   for document. Documents folder contains the document and metadata.json file about the document.
* Util Documents -- Util documents can be either command or automation document. It would have same folder hierarchy and
 requirements as Test document above.

# Metadata.json file
Example :
{
    "documentName": "Digito-AddNetworkLatencyUsingAppliance",
    "documentType": "Automation",
    "documentContentPath": "Digito-AddNetworkLatencyUsingAppliance.yml",
    "documentFormat": "YAML",
    "attachments": "digito_gameday_primitives.zip",
    "dependsOn": "Digito-SetupEC2Appliance,Digito-RouteThroughAppliance,Digito-AddNetworkLatency"
}

* documentName -- Name of document
* documentType -- Command or Automation
* documentContentPath -- Document file name
* documentFormat -- YAML or JSON
* attachments -- Script attachment if required for document
* dependsOn -- Add other documents that this document requires.

# Adding new python script
* Install requirements by running 'pip install -r requirements.txt'
* Add new scripts to documents/util/scripts/src folder and corresponding unit test to documents/util/scripts/test
* Run unit tests by running 'coverage run setup.py test'
* Look at test coverage report by running 'coverage report -m' and detailed report by running 'coverage html'

# Running Integration Tests
* New
  TBD. Explore cucumber based automation tests to setup sample app and run tests.

* Old(To be deprecated as it requires internal ssm process)
Public SSM document team maintains the process for running tests at https://quip-amazon.com/1bjBAZ3I7UQx/Documents-Testing-Framework-Guide

# Work Around for Running Integration Tests
After modifying a document, the above process will need to build two brazil workspaces, which takes a while. The following is a workaround for fast development:
* Copy the whole TestingFramework directory from https://code.amazon.com/packages/SsmDocument/trees/mainline/--/PublicDocuments/TestingFramework to a local directory
* Add TestingFramework to your PYTHONPATH
* Modify method get_credentail_pair() to directly return AWS credential pair in the form of ('publicAccessKey','privateAccessKey'). The function lives in service_client.py under TestingFramework
* Run tests, e.g. python test_document.py
