PRAGMA foreign_keys = ON;

CREATE TABLE Machine(
    machine_id integer PRIMARY KEY AUTOINCREMENT,
    machine_name text NOT NULL UNIQUE,
    x_over integer NULL DEFAULT NULL,
    y_over integer NULL DEFAULT NULL,
    z_over integer NULL DEFAULT NULL,
    x_fspeed integer NULL DEFAULT NULL,
    y_fspeed integer NULL DEFAULT NULL,
    z_fspeed integer NULL DEFAULT NULL,
    input_catalog text NOT NULL,
    output_catalog text NOT NULL,
    CONSTRAINT check_input_catalog CHECK (input_catalog NOT LIKE ""),
    CONSTRAINT check_output_catalog CHECK (output_catalog NOT LIKE "")
);


CREATE TABLE Operation(
    opid blob DEFAULT (randomblob(16)) PRIMARY KEY,
    operation_type text,
    operation_name text NOT NULL,
    target text NOT NULL,
    after_or_before NOT NULL,
    item text NOT NULL,
    CONSTRAINT type_choice CHECK(operation_type IN("a", "r", "d", "c")),
    CONSTRAINT a_or_b CHECK(after_or_before IN("a", "b"))
);


CREATE TABLE Task(
    taskid blob DEFAULT (randomblob(16)) PRIMARY KEY,
    machine_id integer NOT NULL,
    operation_id blob NULL,
    task_name text NOT NULL,
    task_desc NULL DEFAULT "",
    from_t timestamp DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (machine_id) REFERENCES Machine (machine_id)
    ON DELETE CASCADE,
    FOREIGN KEY (operation_id) REFERENCES Operation (opid)
    ON DELETE SET NULL
);

CREATE TABLE User(
    id integer PRIMARY KEY AUTOINCREMENT,
    username text NOT NULL,
    password blob
);

CREATE TABLE Stat(
    id blob DEFAULT (randomblob(16)) PRIMARY KEY

);
