from sqlalchemy import DDL
from models import db


def init_operation_delegation_table_triggers():
    db.engine.execute("""
        CREATE OR REPLACE FUNCTION check_unique_delegation() RETURNS trigger
        AS $body$
        BEGIN
            IF EXISTS(SELECT 1
            FROM operation
            WHERE conditionid=NEW.conditionid OR conditionid IS NULL
            AND insertid=NEW.insertid OR insertid IS NULL
            AND commentid=NEW.commentid OR commentid IS NULL
            AND uncommentid=NEW.uncommentid OR uncommentid IS NULL
            AND removeid=NEW.removeid OR removeid IS NULL
            AND renameid=NEW.renameid OR renameid IS NULL
            AND replaceid=NEW.replaceid OR replaceid IS NULL
            AND numerationid=NEW.numerationid OR numerationid IS NULL
            ) THEN
                RAISE EXCEPTION 'Данный экземпляр сущности уже существует';
            ELSE
                RETURN NEW;
            END IF;
        END; $body$
        LANGUAGE PLPGSQL 
    """)

    db.engine.execute("""
        CREATE TRIGGER operation_delegation_trigger
        BEFORE INSERT OR UPDATE
        ON operation FOR EACH ROW
        EXECUTE PROCEDURE check_unique_delegation();
    """)

    db.engine.execute("""
            CREATE OR REPLACE FUNCTION check_count_delegation_options() RETURNS trigger
            AS $body$
            DECLARE
                counter smallint := 0;
            BEGIN
                SELECT counter + (CASE WHEN NEW.conditionid IS NOT NULL THEN 1 ELSE 0 END) INTO counter;
                SELECT counter + (CASE WHEN NEW.insertid IS NOT NULL THEN 1 ELSE 0 END) INTO counter;
                SELECT counter + (CASE WHEN NEW.commentid IS NOT NULL THEN 1 ELSE 0 END) INTO counter;
                SELECT counter + (CASE WHEN NEW.uncommentid IS NOT NULL THEN 1 ELSE 0 END) INTO counter;
                SELECT counter + (CASE WHEN NEW.removeid IS NOT NULL THEN 1 ELSE 0 END) INTO counter;
                SELECT counter + (CASE WHEN NEW.renameid IS NOT NULL THEN 1 ELSE 0 END) INTO counter;
                SELECT counter + (CASE WHEN NEW.replaceid IS NOT NULL THEN 1 ELSE 0 END) INTO counter;
                SELECT counter + (CASE WHEN NEW.numerationid IS NOT NULL THEN 1 ELSE 0 END) INTO counter;
                IF counter = 0 THEN
                    RAISE EXCEPTION 'Не указана опция для операции';
                ELSEIF counter > 1 THEN
                    RAISE EXCEPTION 'Указано больше одной опции для операции';
                ELSE
                    RETURN NEW;
                END IF;             
            END; $body$
            LANGUAGE PLPGSQL 
        """)

    db.engine.execute("""
            CREATE TRIGGER delegation_trigger_counter
            BEFORE INSERT OR UPDATE
            ON operation FOR EACH ROW
            EXECUTE PROCEDURE check_count_delegation_options();
        """)


def init_cnc_table_triggers():
    db.engine.execute("""
        CREATE OR REPLACE FUNCTION tets_unique_cnc() RETURNS trigger
        AS $body$
        BEGIN
            IF EXISTS(SELECT 1
            FROM cnc
            WHERE name=NEW.name 
            AND comment_symbol=NEW.comment_symbol
            AND except_symbols=NEW.except_symbols OR except_symbols IS NULL
            ) THEN
                RAISE EXCEPTION 'Данный экземпляр сущности уже существует';
            ELSE
                RETURN NEW;
            END IF;
        END; $body$
        LANGUAGE PLPGSQL
    """)

    db.engine.execute("""
        CREATE TRIGGER unique_cnc_control
        BEFORE INSERT OR UPDATE
        ON cnc FOR EACH ROW
        EXECUTE PROCEDURE tets_unique_cnc();
        """)


def init_condition_table_triggers():
    db.engine.execute("""
    CREATE OR REPLACE FUNCTION control_self_parent_condition() RETURNS trigger
    AS $body$
    BEGIN
        IF NEW.parent IS NOT NULL AND NEW.parent=NEW.cnd THEN
            RAISE EXCEPTION 'Невозможна привязка условия самого на себя';
        ELSE
            RETURN NEW;
        END IF;
    END; $body$
    LANGUAGE PLPGSQL
    """)

    db.engine.execute("""
        CREATE TRIGGER check_self_parent_condition
        BEFORE INSERT OR UPDATE
        ON cond FOR EACH ROW
        EXECUTE PROCEDURE control_self_parent_condition();
        """)

    db.engine.execute("""
        CREATE OR REPLACE FUNCTION check_condition() RETURNS trigger
        AS $body$
        BEGIN
            IF EXISTS(
                SELECT 1
                FROM cond
                WHERE parent=NEW.parent OR parent IS NULL 
                AND targetstr=NEW.targetstr
                AND isntfind=NEW.isntfind
                AND findfull=NEW.findfull
                AND findpart=NEW.findpart
                AND conditionbasevalue=NEW.conditionbasevalue
            ) THEN
                RAISE EXCEPTION 'Данный экземпляр сущности уже существует!';
            ELSE
                RETURN NEW;
            END IF;
        END; $body$
        LANGUAGE PLPGSQL
        """)

    db.engine.execute("""
        CREATE TRIGGER check_unique_condition
        BEFORE INSERT OR UPDATE
        ON cond FOR EACH ROW
        EXECUTE PROCEDURE check_condition();
        """)

    db.engine.execute("""
            CREATE OR REPLACE FUNCTION check_condition_options() RETURNS trigger
            AS $body$
            DECLARE
                counter smallint := 0;
            BEGIN
                SELECT counter + (CASE WHEN NEW.isntfind THEN 1 ELSE 0 END) INTO counter;
                SELECT counter + (CASE WHEN NEW.findfull THEN 1 ELSE 0 END) INTO counter;
                SELECT counter + (CASE WHEN NEW.findpart THEN 1 ELSE 0 END) INTO counter;
                IF counter != 1
                THEN
                    RAISE EXCEPTION 'Невалидное состояние опций isntfind, findfull и findpart!';
                ELSE
                    RETURN NEW;
                END IF;
            END; $body$
            LANGUAGE PLPGSQL
            """)

    db.engine.execute("""
        CREATE TRIGGER check_condition_values
        BEFORE INSERT OR UPDATE
        ON cond FOR EACH ROW
        EXECUTE PROCEDURE check_condition_options();
    """)


def init_numeration_table_triggers():
    db.engine.execute("""
        CREATE OR REPLACE FUNCTION check_num_options() RETURNS trigger
        AS $body$
        BEGIN
            IF EXISTS(
                SELECT 1
                FROM num
                WHERE startat=NEW.startat OR startat IS NULL
                AND endat=NEW.endat OR endat IS NULL
            ) THEN
                RAISE EXCEPTION 'Данный экземпляр сущности уже существует';
            ELSE
                RETURN NEW;
            END IF;
        END; $body$
        LANGUAGE PLPGSQL
        """)

    db.engine.execute("""
        CREATE TRIGGER check_unique_num 
        BEFORE INSERT OR UPDATE
        ON num FOR EACH ROW
        EXECUTE PROCEDURE check_num_options();
        """)


def init_replace_table_triggers():
    db.engine.execute("""
        CREATE OR REPLACE FUNCTION check_repl_options() RETURNS trigger
        AS $body$
        BEGIN
            IF EXISTS(
                SELECT 1
                FROM repl
                WHERE findstr=NEW.findstr 
                AND iffullmatch=NEW.iffullmatch
                AND ifcontains=NEW.ifcontains
                AND item=NEW.item
            ) THEN
                RAISE EXCEPTION 'Данный экземпляр сущности уже существует';
            ELSE
                RETURN NEW;
            END IF;
        END; $body$
        LANGUAGE PLPGSQL
        """)

    db.engine.execute("""
        CREATE TRIGGER check_unique_replace
        BEFORE INSERT OR UPDATE
        ON repl FOR EACH ROW
        EXECUTE PROCEDURE check_repl_options();
        """)


def init_comment_table_triggers():
    db.engine.execute("""
        CREATE OR REPLACE FUNCTION check_comm_options() RETURNS trigger
        AS $body$
        BEGIN
            IF EXISTS(
                SELECT 1
                FROM comment
                WHERE findstr=NEW.findstr 
                AND iffullmatch=NEW.iffullmatch
                AND ifcontains=NEW.ifcontains
            ) THEN
                RAISE EXCEPTION 'Данный экземпляр сущности уже существует';
            ELSE
                RETURN NEW;
            END IF;
        END; $body$
        LANGUAGE PLPGSQL
        """)

    db.engine.execute("""
        CREATE TRIGGER check_unique_comment
        BEFORE INSERT OR UPDATE
        ON comment FOR EACH ROW
        EXECUTE PROCEDURE check_comm_options();
        """)

    db.engine.execute(DDL("""
        CREATE OR REPLACE FUNCTION comment_trigger_func() RETURNS trigger
        AS $body$
        DECLARE
            counter smallint := 0;
        BEGIN
            /* Обе опции iffullmatch и ifcontains включены или выключены одновременно */
            SELECT counter + (CASE WHEN NEW.iffullmatch THEN 1 ELSE 0 END) INTO counter;
            SELECT counter + (CASE WHEN NEW.ifcontains THEN 1 ELSE 0 END) INTO counter;
            IF counter != 1 THEN
                RAISE EXCEPTION 'Невалидные опции iffullmatch и ifcontains';
            ELSE
                RETURN NEW;
            END IF;
        END; $body$
        LANGUAGE PLPGSQL
        """))

    db.engine.execute(DDL("""
        CREATE TRIGGER comment_trigger
        BEFORE INSERT OR UPDATE
        ON comment FOR EACH ROW
        EXECUTE PROCEDURE comment_trigger_func();
    """))


def init_remove_table_triggers():
    db.engine.execute("""
        CREATE OR REPLACE FUNCTION check_rem_options() RETURNS trigger
        AS $body$
        BEGIN
            IF EXISTS(
                SELECT 1
                FROM uncomment
                WHERE findstr=NEW.findstr 
                AND iffullmatch=NEW.iffullmatch
                AND ifcontains=NEW.ifcontains
            ) THEN
                RAISE EXCEPTION 'Данный экземпляр сущности уже существует';
            ELSE
                RETURN NEW;
            END IF;
        END; $body$
        LANGUAGE PLPGSQL
        """)

    db.engine.execute("""
            CREATE TRIGGER check_unique_remove
            BEFORE INSERT OR UPDATE
            ON remove FOR EACH ROW
            EXECUTE PROCEDURE check_rem_options();
            """)

    db.engine.execute(DDL("""
        CREATE OR REPLACE FUNCTION remove_trigger_func() RETURNS trigger
        AS $body$
        DECLARE
            counter smallint := 0;
        BEGIN
            /* Обе опции iffullmatch и ifcontains включены или выключены одновременно */
            SELECT counter + (CASE WHEN NEW.iffullmatch THEN 1 ELSE 0 END) INTO counter;
            SELECT counter + (CASE WHEN NEW.ifcontains THEN 1 ELSE 0 END) INTO counter;
            IF counter != 1
            THEN 
                RAISE EXCEPTION 'Невалидные опции iffullmatch и ifcontains';
            ELSE
                RETURN NEW;
            END IF;
        END; $body$
        LANGUAGE PLPGSQL
        """))

    db.engine.execute(DDL("""
        CREATE TRIGGER remove_trigger
        BEFORE INSERT OR UPDATE
        ON remove FOR EACH ROW
        EXECUTE PROCEDURE remove_trigger_func();
    """))


def init_uncomment_table_triggers():
    db.engine.execute("""
        CREATE OR REPLACE FUNCTION check_uncomment_options() RETURNS trigger
        AS $body$
        BEGIN
            IF EXISTS(
                SELECT 1
                FROM uncomment
                WHERE findstr=NEW.findstr 
                AND iffullmatch=NEW.iffullmatch
                AND ifcontains=NEW.ifcontains
            ) THEN
                RAISE EXCEPTION 'Данный экземпляр сущности уже существует';
            ELSE
                RETURN NEW;
            END IF;
        END; $body$
        LANGUAGE PLPGSQL
        """)

    db.engine.execute("""
        CREATE TRIGGER check_unique_uncomment 
        BEFORE INSERT OR UPDATE
        ON uncomment FOR EACH ROW
        EXECUTE PROCEDURE check_uncomment_options();
        """)

    db.engine.execute(DDL("""
        CREATE OR REPLACE FUNCTION uncomment_trigger_func() RETURNS trigger
        AS $body$
        DECLARE
            counter smallint := 0;
        BEGIN
            /* Обе опции iffullmatch и ifcontains включены или выключены одновременно */
            SELECT counter + (CASE WHEN NEW.iffullmatch THEN 1 ELSE 0 END) INTO counter;
            SELECT counter + (CASE WHEN NEW.ifcontains THEN 1 ELSE 0 END) INTO counter;
            IF NOT counter = 1 THEN RAISE EXCEPTION 'Невалидные опции iffullmatch и ifcontains';
            END IF;
            RETURN NEW;
        END; $body$
        LANGUAGE PLPGSQL
        """))

    db.engine.execute(DDL("""
        CREATE TRIGGER uncomment_trigger
        BEFORE INSERT OR UPDATE
        ON uncomment FOR EACH ROW
        EXECUTE PROCEDURE uncomment_trigger_func();
    """))


def init_rename_table_triggers():
    db.engine.execute("""
    CREATE OR REPLACE FUNCTION rename_count_instances() RETURNS trigger
    AS $body$
    BEGIN
        IF EXISTS(
            SELECT 1
            FROM renam 
            WHERE uppercase=NEW.uppercase 
            AND lowercase=NEW.lowercase 
            AND prefix=NEW.prefix OR prefix IS NULL
            AND postfix=NEW.postfix OR postfix IS NULL
            AND nametext=NEW.nametext OR nametext IS NULL
            AND removeextension=NEW.removeextension
            AND setextension=NEW.setextension OR setextension IS NULL
            ) THEN
                RAISE EXCEPTION 'Данный экземпляр сущности уже существует';
            ELSE
                RETURN NEW;
            END IF;
    END; $body$
    LANGUAGE PLPGSQL
    """)

    db.engine.execute("""
    CREATE TRIGGER check_unique_instance_rename
    BEFORE INSERT OR UPDATE
    ON renam FOR EACH ROW
    EXECUTE PROCEDURE rename_count_instances();
    """)

    db.engine.execute(DDL("""
        CREATE OR REPLACE FUNCTION rename_filter_values() RETURNS trigger
        AS $body$
        DECLARE
            all_options_counter smallint := 0;
            ext_counter smallint := 0;
            case_counter smallint := 0;
        BEGIN
            /* Опции "расширение": убрать, установить */
            SELECT ext_counter + (CASE WHEN NEW.removeextension THEN 1 ELSE 0 END) INTO ext_counter;
            SELECT ext_counter + (CASE WHEN NEW.setextension IS NULL THEN 0 ELSE 1 END) INTO ext_counter;
            IF ext_counter > 1 THEN RAISE EXCEPTION 'Мультизначение для опций (removeextension, setextension) недопустимо!';
            END IF;
            /* Опции: uppercase, lowercase */
            SELECT case_counter + (CASE WHEN NEW.uppercase THEN 1 ELSE 0 END) INTO case_counter;
            SELECT case_counter + (CASE WHEN NEW.lowercase THEN 1 ELSE 0 END) INTO case_counter;
            IF case_counter > 1 THEN RAISE EXCEPTION 'Мультизначение для опций (uppercase, lowercase) недопустимо!';
            END IF;
            /* Проверка всех опций на пустые значения */
            SELECT all_options_counter + ext_counter INTO all_options_counter;
            SELECT all_options_counter + case_counter INTO all_options_counter;
            SELECT all_options_counter + (CASE WHEN NEW.prefix IS NULL THEN 0 ELSE 1 END) INTO all_options_counter;
            SELECT all_options_counter + (CASE WHEN NEW.postfix IS NULL THEN 0 ELSE 1 END) INTO all_options_counter;
            select all_options_counter + (CASE WHEN NEW.nametext IS NULL THEN 0 ELSE 1 END) INTO all_options_counter;
            IF all_options_counter = 0 THEN RAISE EXCEPTION 'Все опции выключены';
            END IF;
            RETURN NEW;
        END; $body$
        LANGUAGE PLPGSQL
        """))

    db.engine.execute(DDL("""
        CREATE TRIGGER rename_trigger
        BEFORE INSERT OR UPDATE
        ON renam FOR EACH ROW
        EXECUTE PROCEDURE rename_filter_values();
    """))


def init_insert_table_triggers():
    db.engine.execute("""
    CREATE OR REPLACE FUNCTION insert_count_instances() RETURNS trigger
    AS $body$
    BEGIN
        IF EXISTS(
            SELECT 1
            FROM insert
            WHERE after=NEW.after
            AND before=NEW.before
            AND target=NEW.target 
            AND item=NEW.item
            ) THEN
                RAISE EXCEPTION 'Данный экземпляр сущности уже существует';
            ELSE
                RETURN NEW;
            END IF;
    END; $body$
    LANGUAGE PLPGSQL
    """)

    db.engine.execute("""
    CREATE TRIGGER check_unique_instance_insert
    BEFORE INSERT OR UPDATE
    ON renam FOR EACH ROW
    EXECUTE PROCEDURE insert_count_instances();
    """)

    db.engine.execute(DDL("""
        CREATE OR REPLACE FUNCTION insert_filter_values() RETURNS trigger
        AS $body$
        DECLARE
            counter smallint := 0;
        BEGIN
            SELECT counter + (CASE WHEN NEW.after THEN 1 ELSE 0 END) INTO counter;
            SELECT counter + (CASE WHEN NEW.before THEN 1 ELSE 0 END) INTO counter;
            IF counter != 1
            THEN
                RAISE EXCEPTION 'Опции after и before не могут одновременно иметь одинаковое состояние!';
            ELSE
                RETURN NEW;
            END IF;
        END; $body$
        LANGUAGE PLPGSQL
        """))

    db.engine.execute(DDL("""
        CREATE TRIGGER insert_trigger
        BEFORE INSERT OR UPDATE
        ON renam FOR EACH ROW
        EXECUTE PROCEDURE insert_filter_values();
    """))


if __name__ == "__main__":
    init_rename_table_triggers()
    init_uncomment_table_triggers()
    init_remove_table_triggers()
    init_comment_table_triggers()
    init_replace_table_triggers()
    init_numeration_table_triggers()
    init_condition_table_triggers()
    init_cnc_table_triggers()
    init_insert_table_triggers()
    init_operation_delegation_table_triggers()
