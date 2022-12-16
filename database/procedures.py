from sqlalchemy import DDL
from models import db


def init_operation_delegation_table_triggers():
    db.engine.execute("""
        CREATE OR REPLACE FUNCTION check_unique_delegation() RETURNS trigger
        AS $body$
        BEGIN
            IF EXISTS(SELECT 1
            FROM operation
            WHERE (conditionid=NEW.conditionid OR NEW.conditionid IS NULL AND conditionid IS NULL)
            AND (insertid=NEW.insertid OR NEW.insertid IS NULL AND insertid IS NULL)
            AND (commentid=NEW.commentid OR NEW.commentid IS NULL AND commentid IS NULL)
            AND (uncommentid=NEW.uncommentid OR NEW.uncommentid IS NULL AND uncommentid IS NULL)
            AND (removeid=NEW.removeid OR NEW.removeid IS NULL AND removeid IS NULL)
            AND (renameid=NEW.renameid OR NEW.renameid IS NULL AND renameid IS NULL)
            AND (replaceid=NEW.replaceid OR NEW.replaceid IS NULL AND replaceid IS NULL)
            AND (numerationid=NEW.numerationid OR NEW.numerationid IS NULL AND numerationid IS NULL)
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
            IF (SELECT 1
            FROM cnc
            WHERE name=NEW.name 
            AND comment_symbol=NEW.comment_symbol 
            AND (except_symbols=NEW.except_symbols OR NEW.except_symbols IS NULL AND except_symbols IS NULL)
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
                WHERE (parent=NEW.parent OR NEW.parent IS NULL AND parent IS NULL)
                AND conditiontrue=NEW.conditiontrue
                AND conditionfalse=NEW.conditionfalse
                AND conditionstring=NEW.conditionstring
                AND conditionvalue=NEW.conditionvalue
                AND isntfindfull=NEW.isntfindfull
                AND isntfindpart=NEW.isntfindpart
                AND findfull=NEW.findfull
                AND findpart=NEW.findpart
                AND parentconditiontrue=NEW.parentconditiontrue
                AND parentconditionfalse=NEW.parentconditionfalse
                AND equal=NEW.equal
                AND less=NEW.less
                AND larger=NEW.larger
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
            SELECT counter + (CASE WHEN NEW.isntfindfull THEN 1 ELSE 0 END) INTO counter;
            SELECT counter + (CASE WHEN NEW.isntfindpart THEN 1 ELSE 0 END) INTO counter;
            SELECT counter + (CASE WHEN NEW.findfull THEN 1 ELSE 0 END) INTO counter;
            SELECT counter + (CASE WHEN NEW.findpart THEN 1 ELSE 0 END) INTO counter;
            SELECT counter + (CASE WHEN NEW.equal THEN 1 ELSE 0 END) INTO counter;
            SELECT counter + (CASE WHEN NEW.less THEN 1 ELSE 0 END) INTO counter;
            SELECT counter + (CASE WHEN NEW.larger THEN 1 ELSE 0 END) INTO counter;
            IF counter != 1
            THEN
                RAISE EXCEPTION 'Невалидное состояние опций isntfind, findfull, findpart, less, equal, larger!';
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

    db.engine.execute("""
    CREATE OR REPLACE FUNCTION check_parent_condition() RETURNS trigger
    AS $body$
    DECLARE
        counter smallint := 0;
    BEGIN
        IF NEW.parent IS NOT NULL
        THEN
            SELECT counter + (CASE WHEN NEW.parentconditiontrue THEN 1 ELSE 0 END) INTO counter;
            SELECT counter + (CASE WHEN NEW.parentconditionfalse THEN 1 ELSE 0 END) INTO counter;
            IF counter != 1 THEN 
                RAISE EXCEPTION 'Недействительные опции для родительского условия';
                END IF;
        END IF;
    END; $body$
    LANGUAGE PLPGSQL
    """)

    db.engine.execute("""
    CREATE TRIGGER check_parent_condition_if
    BEFORE INSERT OR UPDATE
    ON cond FOR EACH ROW
    EXECUTE PROCEDURE check_parent_condition();
    """)


def init_numeration_table_triggers():
    db.engine.execute("""
        CREATE OR REPLACE FUNCTION check_num_options() RETURNS trigger
        AS $body$
        BEGIN
            IF EXISTS(
                SELECT 1
                FROM num
                WHERE startat=NEW.startat
                AND (endat=NEW.endat OR NEW.endat IS NULL AND endat IS NULL)
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
            AND (prefix=NEW.prefix OR NEW.prefix IS NULL AND prefix IS NULL)
            AND (postfix=NEW.postfix OR NEW.postfix IS NULL AND postfix IS NULL)
            AND (nametext=NEW.nametext OR NEW.nametext IS NULL AND nametext IS NULL)
            AND removeextension=NEW.removeextension
            AND (setextension=NEW.setextension OR NEW.setextension IS NULL AND setextension IS NULL)
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
    ON insert FOR EACH ROW
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
        ON insert FOR EACH ROW
        EXECUTE PROCEDURE insert_filter_values();
    """))


def init_machine_table_triggers():
    db.engine.execute("""
        CREATE OR REPLACE FUNCTION machine_count_instances() RETURNS trigger
        AS $body$
        BEGIN
            IF EXISTS(
                SELECT 1
                FROM machine
                WHERE (cncid=NEW.cncid OR NEW.cncid IS NULL AND cncid IS NULL)
                AND machine_name=NEW.machine_name
                AND (x_over=NEW.x_over OR NEW.x_over IS NULL AND x_over IS NULL)
                AND (y_over=NEW.y_over OR NEW.y_over IS NULL AND y_over IS NULL)
                AND (z_over=NEW.z_over OR NEW.z_over IS NULL AND z_over IS NULL)
                AND (x_fspeed=NEW.x_fspeed OR NEW.x_fspeed IS NULL AND x_fspeed IS NULL)
                AND (y_fspeed=NEW.y_fspeed OR NEW.y_fspeed IS NULL AND y_fspeed IS NULL)
                AND (z_fspeed=NEW.z_fspeed OR NEW.z_fspeed IS NULL AND z_fspeed IS NULL)
                AND (spindele_speed=NEW.spindele_speed OR NEW.spindele_speed IS NULL AND spindele_speed IS NULL)
                AND input_catalog=NEW.input_catalog
                AND output_catalog=NEW.output_catalog
                ) THEN
                    RAISE EXCEPTION 'Данный экземпляр сущности уже существует';
                ELSE
                    RETURN NEW;
                END IF;
        END; $body$
        LANGUAGE PLPGSQL
        """)

    db.engine.execute("""
        CREATE TRIGGER check_machine
        BEFORE INSERT OR UPDATE
        ON machine FOR EACH ROW
        EXECUTE PROCEDURE machine_count_instances();
        """)


def init_headvarible_table_triggers():
    db.engine.execute("""
        CREATE OR REPLACE FUNCTION headvarible_count_instances() RETURNS trigger
        AS $body$
        BEGIN
            IF EXISTS(
                SELECT 1
                FROM headvar
                WHERE name=NEW.name
                AND separator=new.separator
                AND select_all=NEW.select_all
                AND select_numbers=NEW.select_numbers
                AND select_string=NEW.select_string
                AND select_reg=NEW.select_reg 
                ) THEN
                    RAISE EXCEPTION 'Данный экземпляр сущности уже существует';
                ELSE
                    RETURN NEW;
                END IF;
        END; $body$
        LANGUAGE PLPGSQL
        """)

    db.engine.execute("""
        CREATE TRIGGER check_headvarible
        BEFORE INSERT OR UPDATE
        ON headvar FOR EACH ROW
        EXECUTE PROCEDURE headvarible_count_instances();
        """)

    db.engine.execute("""
        CREATE OR REPLACE FUNCTION headvar_check_select_options() RETURNS trigger
        AS $body$
        DECLARE
            select_counter smallint := 0;
            isnotexists_counter smallint := 0;
        BEGIN
            SELECT select_counter + (CASE WHEN NEW.select_all THEN 1 ELSE 0 END) INTO select_counter;
            SELECT select_counter + (CASE WHEN NEW.select_numbers THEN 1 ELSE 0 END) INTO select_counter;
            SELECT select_counter + (CASE WHEN NEW.select_string THEN 1 ELSE 0 END) INTO select_counter;
            SELECT select_counter + (CASE WHEN NEW.select_reg IS NOT NULL THEN 1 ELSE 0 END) INTO select_counter;
            SELECT isnotexists_counter + (CASE WHEN NEW.isnotexistsdonothing THEN 1 ELSE 0 END) INTO isnotexists_counter;
            SELECT isnotexists_counter + (CASE WHEN NEW.isnotexistsvalue IS NOT NULL THEN 1 ELSE 0 END) INTO isnotexists_counter;
            SELECT isnotexists_counter + (CASE WHEN NEW.isnotexistsbreak THEN 1 ELSE 0 END) INTO isnotexists_counter;
            IF isnotexists_counter != 1 THEN
                RAISE EXCEPTION 'Недействительные опции isnotexists*, - не выбрано ни одной, или выбрано несколько';
            END IF;
            IF select_counter != 1 THEN
                RAISE EXCEPTION 'Недействительные опции select_*, - не выбрано ни одной, или выбрано несколько';
            END IF;
            RETURN NEW;
        END; $body$
        LANGUAGE PLPGSQL
        """)

    db.engine.execute("""
        CREATE TRIGGER check_headvarible_select_options
        BEFORE INSERT OR UPDATE
        ON headvar FOR EACH ROW
        EXECUTE PROCEDURE headvar_check_select_options();
        """)


def init_headvardelegation_table_triggers():
    db.engine.execute("""
        CREATE OR REPLACE FUNCTION varsec_check_unique() RETURNS trigger
        AS $body$
        BEGIN
            IF EXISTS(SELECT 1
                FROM varsec
                WHERE varid=NEW.varid
                AND (insertid=NEW.insertid OR NEW.insertid IS NULL AND insertid IS NULL)
                AND (renameid=NEW.renameid OR NEW.renameid IS NULL AND renameid IS NULL)
            ) THEN 
                RAISE EXCEPTION 'Данный экземпляр сущности уже существует';
            ELSE
                RETURN NEW;
            END IF;
        END; $body$
        LANGUAGE PLPGSQL
        """)

    db.engine.execute("""
        CREATE TRIGGER check_varsec_instance
        BEFORE INSERT OR UPDATE
        ON varsec FOR EACH ROW
        EXECUTE PROCEDURE varsec_check_unique();
        """)

    db.engine.execute("""
        CREATE OR REPLACE FUNCTION varsec_check_options() RETURNS trigger
        AS $body$
        DECLARE
            counter smallint := 0;
        BEGIN
            SELECT counter + (CASE WHEN NEW.insertid IS NOT NULL THEN 1 ELSE 0 END) INTO counter;
            SELECT counter + (CASE WHEN NEW.renameid IS NOT NULL THEN 1 ELSE 0 END) INTO counter;
            IF counter != 1 THEN
                RAISE EXCEPTION 'Недействительные опции для FK*, - не выбрано ни одной, или выбрано несколько';
            ELSE
                RETURN NEW;
            END IF;
        END; $body$
        LANGUAGE PLPGSQL
        """)

    db.engine.execute("""
        CREATE TRIGGER check_varsec_options
        BEFORE INSERT OR UPDATE
        ON varsec FOR EACH ROW
        EXECUTE PROCEDURE varsec_check_options();
        """)


def init_taskdelegation_table_triggers():
    db.engine.execute("""
        CREATE OR REPLACE FUNCTION taskdelegate_check_unique() RETURNS trigger
        AS $body$
        BEGIN
            IF EXISTS(SELECT 1
            FROM taskdelegate
            WHERE machineid=NEW.machineid
            AND operationid=NEW.operationid) THEN 
                RAISE EXCEPTION 'Данный экземпляр сущности уже существует';
            ELSE
                RETURN NEW;
            END IF;
        END; $body$
        LANGUAGE PLPGSQL
        """)

    db.engine.execute("""
        CREATE TRIGGER check_taskdelegate_instance
        BEFORE INSERT OR UPDATE
        ON taskdelegate FOR EACH ROW
        EXECUTE PROCEDURE taskdelegate_check_unique();
        """)


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
    init_machine_table_triggers()
    init_headvarible_table_triggers()
    init_headvardelegation_table_triggers()
    init_taskdelegation_table_triggers()
