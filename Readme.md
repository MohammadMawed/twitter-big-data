## Preliminary

You need [pipenv](https://pipenv.pypa.io/en/latest/) to run the project. If you use our
Vagrant VM, please run the following command inside the VM. But if you are like me not using VM then just skip the VM part and follow my guide:
```
pip install --user --break-system-packages pipenv
```
If you use our Docker container, please run the following command inside the container:
```
pip install --user pipenv
```

If you are using Windows as OS, you should use the PowerShell to install pipenv and
run the project.

## Installation

Install the project using pipenv in the directory where the `Pipfile` resides. The command

```
pipenv install
```

will create a virtual environment and install the required dependencies. When using an IDE like
PyCharm you want o make sure that that virtual environment is used for the project.

Then
```
pipenv shell
```
will activate that virtual environment.

After working on the project, the virtual environment can be deactivated again using the
```
exit
```
command.

## Without VM

Install dependencies manually using pip. Refer to the Pipfile for the list of dependencies, use the following command:

```
pip install django djangorestframework faker termcolor regex
```


Before running the application, you need to apply migrations to set up your database schema. Run:

```
python manage.py migrate
```

(Optional) Load Initial Data

If your application requires initial data or you want to populate the database with fake data for development purposes, use the provided script:

```
./recreate_models_and_data.sh
```
## Running the Server

Start the Development Server

With the database set up, you can start the Django development server:

```
python manage.py runserver
```
The server will start, and you can access the application by navigating to http://127.0.0.1:8000/ in your web browser.


## Unit Tests

To run the unit tests in the virtual environment, use the following command:

```
python manage.py test
```

Recall to disable the failing tests and enable them one by one to see the failing tests. 
Note that the tests use the fixture `database_dump.json`.

## Server

To run the server in the virtual environment, use the following command:

```
python manage.py runserver
```

## Models, Database, and Fake Data

Use the script
```
recreate_models_and_data.sh
```
to recreate the migrations, database, fake data and fixtures.
