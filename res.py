import psycopg2
from sys import argv
import re
import math


class DatabaseConnection:
    def __init__(self):
        try:
            self.conn = psycopg2.connect(
                "dbname='mydb' user='adam' host='localhost' password='123456' port='5432'"
            )
            # self.connection.autocommit = True
            self.cur = self.conn.cursor()
        except:
            print("Could not connect to database!")

    def c(self):
        self.conn.commit()

    def get_query(self, query, error_msg):
        try:
            self.cur.execute(query)
            header = [desc[0] for desc in self.cur.description]
            body = self.cur.fetchall()
            return (body, header)
        except psycopg2.Error as err:
            print(error_msg)
            raise

    def get_konobar_order_prezime(self):
        try:
            self.cur.execute(
                "SELECT z.oib, z.ime, z.prezime FROM zaposlenik AS z INNER JOIN pozicija AS p ON z.pozicija_id = p.id WHERE p.naziv='konobar' AND z.employed = 't' ORDER BY z.prezime")
            header = [desc[0] for desc in self.cur.description]
            body = self.cur.fetchall()
            return (body, header)
        except psycopg2.Error as err:
            print('Failed to get waiters!')
            raise

    def get_menu_item_order_name(self):
        try:
            self.cur.execute(  # !
                "SELECT id, naziv, opis, cijena FROM menu_item ORDER BY naziv")
            header = [desc[0] for desc in self.cur.description]
            body = self.cur.fetchall()
            return (body, header)
        except psycopg2.Error as err:
            print('Failed to get menu items!')
            raise

    def search_employee(self, inp, col):
        str_l = []
        for x in col:
            if x == 'employed' or x == 'pozicija_id':
                str_l.append("z.{} = %s".format(x))
                continue
            str_l.append("LOWER(z.{}) LIKE LOWER(%s) ESCAPE ''".format(x))

        vals = []
        for i, x in enumerate(inp, start=0):
            c = col[i]
            if c == 'employed' or c == 'pozicija_id':
                vals.append(x)
                continue
            vals.append('%{}%'.format(x))
        try:
            q = """SELECT z.oib, z.ime, z.prezime, z.kontakt, z.adresa, (CASE WHEN z.employed = 't' THEN 'da' ELSE 'ne' END) AS zaposlen, p.naziv
                    FROM zaposlenik AS z
                    INNER JOIN pozicija AS p  ON z.pozicija_id = p.id
                    WHERE {}
                    ORDER BY z.prezime""".format(' OR '.join(str_l))
            self.cur.execute(q, vals)
            header = [desc[0] for desc in self.cur.description]
            body = self.cur.fetchall()
            return (body, header)
        except psycopg2.Error as err:
            print("Failed to get searched employees!")
            raise

    def get_stol_order_last_24h(self):
        try:
            self.cur.execute(  # !
                """SELECT id, broj_osoba, to_char(vrijeme_izrade,'HH24:MM:SS') AS vrijeme, vrijeme_izrade::date AS datum
                FROM stol
                WHERE NOW() > vrijeme_izrade::timestamptz
                AND NOW() - vrijeme_izrade::timestamptz <= interval '24 hours'
                ORDER BY vrijeme_izrade DESC""")
            header = [desc[0] for desc in self.cur.description]
            body = self.cur.fetchall()
            return (body, header)
        except psycopg2.Error as err:
            print('Failed to get tables!')
            raise

    def insert_csv(self, file, db):
        with open(file, 'r') as f:
            next(f)
            self.cur.copy_from(f, 'pets', sep=',')
        self.conn.commit()

    def insert(self, table, cols, vals, returning=''):
        if returning:
            returning = 'RETURNING ' + returning
        try:
            query = "INSERT INTO {} ({}) VALUES ({}) {}".format(
                table, ', '.join(cols), ', '.join(['%s'] * len(vals)), returning)
            self.cur.execute(query, vals)
            self.conn.commit()
            if returning:
                id = self.cur.fetchall()[0]
                return id
            else:
                return 1
        except psycopg2.Error as err:
            self.conn.rollback()
            raise

    def insert_one(self, table, cols, vals, returning=''):
        if returning:
            returning = 'RETURNING ' + returning
        try:
            query = "INSERT INTO {} ({}) VALUES ({}) {}".format(
                table, ', '.join(cols), ', '.join(['%s'] * len(vals)), returning)
            self.cur.execute(query, vals)
            #! self.conn.commit()
            if returning:
                id = self.cur.fetchall()[0]
                return id
            else:
                return 1
        except psycopg2.Error as err:
            self.conn.rollback()
            raise

    def insert_many(self, table, cols, vals, returning=''):
        if returning:
            returning = 'RETURNING ' + returning
        try:
            query = "INSERT INTO {} ({}) VALUES {} {}".format(
                table, ', '.join(cols), ', '.join(['%s'] * len(vals)), returning)
            q = self.cur.mogrify(query, [tuple(v) for v in vals])
            self.cur.execute(q)
            self.conn.commit()

            if returning:
                ids = self.cur.fetchall()
                return ids
            else:
                return 1
        except psycopg2.Error as err:
            self.conn.rollback()
            raise

    def create_table(self, name, query):
        try:
            self.cur.execute('DROP TABLE IF EXISTS {} CASCADE'.format(name))
            self.cur.execute(query)
            # self.conn.commit()
        except psycopg2.Error as err:
            raise

    def populate_table(self, name, header, values):
        try:
            self.cur.execute('SELECT * FROM {}'.format(name))
            query = 'INSERT INTO {} ({}) VALUES ({})'.format(
                name, ', '.join(header), ', '.join(['%s'] * len(header)))
            self.cur.executemany(query, values)
            # self.conn.commit()
        except psycopg2.Error as err:
            raise

    def create_restaurant_tables(self):
        zaposlenik = """CREATE TABLE zaposlenik(
            oib varchar(11)  NOT NULL CHECK (length(oib) = 11) ,
            ime varchar(20)  NOT NULL,
            prezime varchar(20)  NOT NULL,
            kontakt varchar(30)  NOT NULL,
            adresa varchar(50)  NOT NULL,
            employed bool DEFAULT 't' NOT NULL,
            pozicija_id int  NOT NULL REFERENCES pozicija (id),
            CONSTRAINT zaposlenik_pk PRIMARY KEY (oib))"""
        menu_item = """CREATE TABLE menu_item(
            id serial  NOT NULL,
            naziv varchar(50)  NOT NULL,
            opis varchar(500)  NOT NULL,
            cijena decimal(7,2)  NOT NULL,
            menu_item_kategorija_id int  NOT NULL REFERENCES menu_item_kategorija (id),
            CONSTRAINT menu_item_pk PRIMARY KEY (id))"""
        menu_item_kategorija = """CREATE TABLE menu_item_kategorija(
            id serial  NOT NULL,
            naziv varchar(20)  NOT NULL,
            CONSTRAINT menu_item_kategorija_pk PRIMARY KEY (id))"""
        narudzba = """CREATE TABLE narudzba(
            id serial  NOT NULL,
            zaposlenik_oib varchar(11)  NOT NULL REFERENCES zaposlenik (oib),
            stol_id int  NOT NULL REFERENCES stol (id),
            CONSTRAINT narudzba_pk PRIMARY KEY (id))"""
        narudzba_menu_item = """CREATE TABLE narudzba_menu_item(
            id serial  NOT NULL,
            narudzba_id int  NOT NULL REFERENCES narudzba (id),
            menu_item_id int  NOT NULL REFERENCES menu_item (id),
            kolicina smallint  NOT NULL,
            CONSTRAINT narudzba_menu_item_pk PRIMARY KEY (id))"""
        pozicija = """CREATE TABLE pozicija(
            id serial  NOT NULL,
            naziv varchar(15)  NOT NULL,
            CONSTRAINT pozicija_pk PRIMARY KEY (id))"""
        stol = """CREATE TABLE stol(
            id serial  NOT NULL,
            broj_osoba int  NOT NULL,
            vrijeme_izrade timestamp(1) DEFAULT now() NOT NULL,
            CONSTRAINT stol_pk PRIMARY KEY (id))"""
        restoran = """CREATE TABLE restoran(
            naziv varchar(25)  NOT NULL,
            adresa varchar(50)  NOT NULL,
            kontakt varchar(50)  NOT NULL,
            radno_vrijeme varchar(50)  NOT NULL,
            CONSTRAINT restoran_pk PRIMARY KEY (naziv))"""
        try:
            self.create_table('restoran', restoran)
            self.create_table('pozicija', pozicija)
            self.create_table('zaposlenik', zaposlenik)
            self.create_table('stol', stol)
            self.create_table('narudzba', narudzba)
            self.create_table('menu_item_kategorija', menu_item_kategorija)
            self.create_table('menu_item', menu_item)
            self.create_table('narudzba_menu_item', narudzba_menu_item)
            self.conn.commit()
        except psycopg2.Error as err:
            print('Failed to create restaurant tables!')
            self.conn.rollback()
            # raise
        else:
            print('Restaurant tables created successfully!')

    def populate_restaurant_tables(self):
        restoran = (('res', 'unknown street 234',
                     '883482482', 'randno vrijeme...'),)
        pozicije = (('kuhar',), ('konobar',))
        menu_item_kategorije = (('jelo',), ('pice',))
        zaposlenici = (
            ('89402938411', 'Ran', 'Per', '52642', 'Something Street 54', 't', 1),
            ('23892049382', 'Harry', 'Potter',
             '57127', 'Somethadsfreet 43', 't', 2),
            ('33824028842', 'Fdk', 'Kfjkds', '9000', 'Someadft 14', 't', 2),
            ('59394900028', 'Mark', 'Bentley', '29000', 'Sometadftreet 22', 't', 1),
            ('61934802193', 'Tjsdkf', 'Tjksdf',
             '21000', 'Somethadfreet 44', 't', 2),
            ('71705410875', 'Hummer', 'Dkdf', '41400', 'Somethiadsfeet 42', 't', 2),
            ('88994728442', 'Volkswagen', 'Guy',
             '21600', 'Somethadsfreet 34', 't', 2)
        )
        menu_itemi = (
            ('Lignje', 'random opis...', 50.00, 1),
            ('Pizza', 'sir, sunka...', 50.00, 1),
            ('Riba', 'random opis...', 70.00, 1),
            ('Cola', 'random opis...', 15.50, 2)
        )

        try:
            self.populate_table(
                'restoran', ('naziv', 'adresa', 'kontakt', 'radno_vrijeme'), restoran)
            self.populate_table('pozicija', ('naziv',), pozicije)
            self.populate_table('zaposlenik', ('oib', 'ime', 'prezime',
                                               'kontakt', 'adresa', 'employed', 'pozicija_id'), zaposlenici)
            self.populate_table('menu_item_kategorija',
                                ('naziv',), menu_item_kategorije)
            self.populate_table(
                'menu_item', ('naziv', 'opis', 'cijena', 'menu_item_kategorija_id'), menu_itemi)
            self.conn.commit()
        except psycopg2.Error as err:
            print('Failed to populate restaurant tables!')
            self.conn.rollback()
            # raise
        else:
            print('Restaurant tables populated successfully!')

    def insert_order_new_table(self, s_vals, s_cols, n_vals, n_cols, nmi_vals, nmi_cols):
        try:
            stol_id = self.insert('stol', s_cols, s_vals, 'id')
            narudzba_id = self.insert(
                'narudzba', n_cols + ['stol_id'], n_vals + [stol_id], 'id')
            for x in nmi_vals:
                x.append(narudzba_id)
            self.insert_many('narudzba_menu_item', nmi_cols +
                             ['narudzba_id'], nmi_vals)
        except psycopg2.Error as err:
            print('Failed to insert order!')
            self.conn.rollback()
        else:
            print('Order successfully created!')

    def insert_order_existing_table(self, n_vals, n_cols, nmi_vals, nmi_cols):
        try:
            narudzba_id = self.insert('narudzba', n_cols, n_vals, 'id')
            for x in nmi_vals:
                x.append(narudzba_id)
            self.insert_many('narudzba_menu_item', nmi_cols +
                             ['narudzba_id'], nmi_vals)
        except psycopg2.Error as err:
            print('Failed to insert order!')
            self.conn.rollback()
        else:
            print('Order successfully created!')

    def get_pozicija(self):
        try:
            self.cur.execute("SELECT * FROM pozicija")  # !
            header = [desc[0] for desc in self.cur.description]
            body = self.cur.fetchall()
            return (body, header)
        except psycopg2.Error as err:
            print('Failed to get position data!')
            raise

    def get_zaposlenik(self):
        try:
            self.cur.execute(  # !
                "SELECT z.oib, z.ime, z.prezime, z.kontakt, z.adresa, (CASE WHEN z.employed = 't' THEN 'da' ELSE 'ne' END) AS zaposlen, p.naziv AS pozicija FROM zaposlenik AS z INNER JOIN pozicija AS p ON z.pozicija_id = p.id")
            header = [desc[0] for desc in self.cur.description]
            body = self.cur.fetchall()
            return (body, header)
        except psycopg2.Error as err:
            print("Failed to get employee data!")
            raise

    def get_menu_item(self):
        try:
            self.cur.execute(  # !
                'SELECT mi.id, mi.naziv, mi.opis, mi.cijena, mik.naziv FROM menu_item AS mi INNER JOIN menu_item_kategorija AS mik ON mi.menu_item_kategorija_id = mik.id')
            header = [desc[0] for desc in self.cur.description]
            body = self.cur.fetchall()
            return (body, header)
        except psycopg2.Error as err:
            print('Failed to get menu item data!')
            raise

    def get_menu_item_kategorija(self):
        try:
            self.cur.execute(
                "SELECT * FROM menu_item_kategorija")  # !
            header = [desc[0] for desc in self.cur.description]
            body = self.cur.fetchall()
            return (body, header)
        except psycopg2.Error as err:
            print('Failed to get menu item category!')
            raise

    def update_table(self, table, cols, vals, iden, iden_v):
        cols_str = ', '.join(cols)
        if len(cols) > 1:
            cols_str = '(' + cols_str + ')'

        try:
            query = "UPDATE {} SET {} = ({}) WHERE {} = '{}'".format(
                table, cols_str, ', '.join(['%s'] * len(vals)), iden, iden_v)
            self.cur.execute(query, vals)
            self.conn.commit()
        except psycopg2.Error as err:
            self.conn.rollback()
            raise

    def get_table_orders(self, val):

        q = """SELECT
                    n.id narudzba_id,
                    z.ime zaposlenik_ime,
                    z.prezime zaposlenik_prezime,
                    mi.naziv item_naziv,
                    mi.cijena item_cijena,
                    SUM(nmi.kolicina) item_kolicina,
                    SUM(nmi.kolicina) * mi.cijena item_cijena
                FROM
                    stol s
                    INNER JOIN narudzba n ON n.stol_id = s.id
                    INNER JOIN narudzba_menu_item nmi ON nmi.narudzba_id = n.id
                    INNER JOIN menu_item mi ON mi.id = nmi.menu_item_id
                    INNER JOIN zaposlenik z ON z.oib = n.zaposlenik_oib
                    WHERE s.id = %s
                    GROUP BY n.id, z.ime, z.prezime, mi.naziv, mi.cijena
                    ORDER BY n.id"""
        try:
            self.cur.execute(
                'SELECT EXISTS (SELECT 1 FROM pozicija WHERE id = %s)', (val,))
            if not self.cur.fetchall()[0][0]:
                return (False, False)
            self.cur.execute(q, (val,))
            header = [desc[0] for desc in self.cur.description]
            body = self.cur.fetchall()
            return (body, header)
        except psycopg2.Error as err:
            print('Failed to get table orders!')
            raise


def create_options_view(options, label='Options:\n'):
    o = label + '\n'
    for i, x in enumerate(options, start=1):
        o += '\t{}: {}\n'.format(str(i), custom_join('\n\t   ', x['labels']))
    o += 'Choose index: '
    return o


def input_handler(label, nullable, number, options):
    while True:
        r, error_msg = normalize_and_check(
            get_stpd_input(label), nullable, number, options)
        if error_msg is None:
            break
        print(error_msg)
    return r


def normalize_and_check(r, nullable, number, options):
    if r == '' and nullable:
        return ((None, None), None)
    elif r == '' and not nullable:
        return ((None, None), 'Input required!')

    if options:
        if r.isdigit():
            r_int = int(r)
            if r_int < 1 or r_int > len(options):
                return ((None, None), 'Number out of range!')
            r = options[r_int - 1]['index']
            v = options[r_int - 1]['labels']
            return ((r, v), None)
        return ((None, None), 'Index number required!')
    else:
        if number:
            try:
                r_fl = float(r)
            except:
                return ((None, None), 'Numeric input required!')

            if r.isdigit():
                return ((r, r), None)

            if r_fl:
                try:
                    t = number.get('type')
                    if t == 'numeric' or t == 'decimal':
                        prec = number.get('prec', None)
                        if len(str(math.floor(r_fl))) > int(prec):
                            return ((None, None), 'Number too big!')
                except:
                    return ((None, None), 'Numeric input required!')
                else:
                    return ((r, r), None)

                return ((None, None), 'Decimal input required!')

    return ((r, r), None)


def get_stpd_input(label='>'):
    return re.sub('\s+', ' ', input(label).strip())


def get_lc_stpd_input(label='>'):
    return re.sub('\s+', ' ', input(label).lower()).strip()


def custom_join(sep, value):
    if not value:
        return ''
    return sep.join(str(v) for v in ([value] if isinstance(value, (str, int)) else value))


def prepare_label(label, nullable, options=''):
    if nullable:
        label += ' (Not Required): '
    else:
        label += ': '
    if options:
        label = create_options_view(options, label)
    return label


def print_table_ascii(body, header=None):
    if header:
        body = ([tuple(header)] + body)
    max_cols_width = None
    for row in body:
        if not max_cols_width:
            max_cols_width = [len(str(x)) for x in row]
        else:
            max_cols_width = [max(x, len(str(y)))
                              for x, y in zip(max_cols_width, row)]
    sep = '+-{}-+'.format('-+-'.join(['-' *
                                      w for w in max_cols_width]))
    for i, row in enumerate(body, start=1):
        cols = [str(c).ljust(w)
                for w, c in zip(max_cols_width, row)]
        if i == 1 or (i == 2 and header):
            print(sep)
        print('| {} |'.format(' | '.join(list(cols))))
        if i == len(body):
            print(sep)


def print_zaposlenik():
    try:
        body, header = db_conn.get_zaposlenik()
    except psycopg2.Error:
        return
    else:
        if not body:
            print('No employee found!')
            return
        print_table_ascii(body, header)
        input('Press any key to continue...')


def print_pozicija():
    try:
        body, header = db_conn.get_pozicija()
    except psycopg2.Error:
        return
    else:
        if not body:
            print('No position found!')
            return
        print_table_ascii(body, header)
        input('Press any key to continue...')


def print_stol_narudzbe():
    items = ['Options:', '1: Insert table ID',
             '2: Choose a table from last 24h', '0: Back']
    o = '\n    '.join(items)
    show = True

    while True:
        if show:
            print(o)
        show = True
        x = get_lc_stpd_input('Choose index or type text: ')

        if any(v in x for v in ['1', 'ins', 'id']):
            r = digit_input('Table ID: ')
        elif any(v in x for v in ['2', 'tables', 'last', '24']):
            try:
                body, header = db_conn.get_stol_order_last_24h()
            except psycopg2.Error as err:
                return
            else:
                if not body:
                    print('No table in last 24h found!')
                    continue
                options = []
                for x in body:
                    options.append({'index': x[0], 'labels': ('Id: {}'.format(x[0]), 'Broj gostiju: {}'.format(
                        x[1]), 'Vrijeme: {}'.format(x[2]), 'Datum: {}'.format(x[3]))})

            label = create_options_view(options)
            r, v = input_handler(label, False, True, options)
        elif any(v in x for v in ['0', 'bac']):
            return
        else:
            show = False
            print('Wrong input!')
            continue
        break

    try:
        body, header = db_conn.get_table_orders(r)
    except psycopg2.Error:
        return
    else:
        if body == False:
            print("Table with given ID doesn't exist!")
            return
        elif not body:
            print('Given table has no orders!')
            return
        print_table_ascii(body, header)
        input('Press any key to continue...')


def print_stol_order_last_24h():
    try:
        body, header = db_conn.get_stol_order_last_24h()
    except psycopg2.Error:
        return
    else:
        if not body:
            print('No table in last 24h found!')
            return
        print_table_ascii(body, header)
        input('Press any key to continue...')


def i_handler(table_spec, table):
    vals = []
    cols = []
    for x in table_spec:
        label = x['label']
        col = x['col']
        nullable = x['nullable']
        options = x.get('options', None)
        while True:
            l = prepare_label(label, nullable, options)
            r, v = input_handler(l, x['nullable'],
                                 x['number'], x.get('options', None))

            if not additional_check(table, col, r):
                continue

            break
        vals.append(r)
        cols.append(col)
    return (vals, cols)


def additional_check(table, col, r):
    msg = ''
    if table == 'stol':
        if col == 'broj_osoba':
            if not 1 <= int(r) <= 10:
                msg = 'Must be in range of 1 to 10!'
    elif table == 'pozicija':
        if col == 'naziv':
            if not len(r) <= 15:
                msg = 'Limited to 15 characters!'
    elif table == 'menu_item_kategorija':
        if col == 'naziv':
            if not len(r) <= 20:
                msg = 'Limited to 20 characters!'
    elif table == 'menu_item':
        if col == 'naziv':
            if not len(r) <= 50:
                msg = 'Limited to 50 characters!'
        if col == 'opis':
            if not len(r) <= 500:
                msg = 'Limited to 500 characters!'
    elif table == 'narudzba_menu_item':
        if col == 'kolicina':
            if not 1 <= int(r) <= 100:
                msg = 'Must be in range of 1 to 100!'
    elif table == 'narudzba':
        if col == 'stol_id':
            if not 1 <= int(r) <= 32767:
                msg = 'Must be in range of 1 to 32767!'
    elif table == 'zaposlenik':
        if col == 'oib':
            if not len(r) == 11:
                msg = '11 numbers required!'
        elif col == 'ime' or col == 'prezime':
            if not len(r) <= 20:
                msg = 'Limited to 20 characters!'
        elif col == 'kontakt':
            if not len(r) <= 30:
                msg = 'Limited to 30 characters!'
        elif col == 'adresa':
            if not len(r) <= 50:
                msg = 'Limited to 50 characters!'
    elif table == 'restoran':
        if col == 'naziv':
            if not len(r) <= 25:
                msg = 'Limited to 25 characters!'
        elif col == 'adresa' or col == 'kontakt' or col == 'radno_vrijeme':
            if not len(r) <= 50:
                msg = 'Limited to 50 characters!'
    if not msg:
        return True
    else:
        print(msg)
        return False


def stol_form():
    table = 'stol'
    table_spec = [{'col': 'broj_osoba', 'label': 'Broj gostiju',
                   'nullable': False, 'number': True}]
    vals, cols = i_handler(table_spec, table)

    return vals, cols


def narudzba_form():
    table = 'narudzba'
    table_spec = [{'col': 'zaposlenik_oib',
                   'label': 'Zaposlenik', 'nullable': False, 'number': False}]
    try:
        body, header = db_conn.get_konobar_order_prezime()
    except psycopg2.Error as err:
        print('Failed to get zaposlenik data!')
        return
    else:
        if not body:
            print('No waiter found!')
            return
        options = []
        for x in body:
            options.append({'index': x[0], 'labels': (
                'OIB: {}'.format(x[0]), 'Ime: {}'.format(x[1]), 'Prezime: {}'.format(x[2]))})
        table_spec[0].update({'options': options})

    vals, cols = i_handler(table_spec, table)

    return vals, cols


def narudzba_form_existing_table():
    table = 'narudzba'
    table_spec = [{'col': 'zaposlenik_oib', 'label': 'Zaposlenik', 'nullable': False, 'number': False},
                  {'col': 'stol_id', 'label': 'Stol', 'nullable': False, 'number': False}]
    try:
        body_k, header_k = db_conn.get_konobar_order_prezime()
        body_s, header_s = db_conn.get_stol_order_last_24h()
    except psycopg2.Error as err:
        # print(err)
        return
    else:
        if not body_s:
            print('No table in last 24h found!')
            return
        elif not body_k:
            print('No waiter found!')
            return
        options_k = []
        for x in body_k:
            options_k.append({'index': x[0], 'labels': (
                'OIB: {}'.format(x[0]), 'Ime: {}'.format(x[1]), 'Prezime: {}'.format(x[2]))})
        table_spec[0].update({'options': options_k})

        options_s = []
        for x in body_s:
            options_s.append({'index': x[0], 'labels': (
                'Id: {}'.format(x[0]), 'Broj gostiju: {}'.format(x[1]), 'Vrijeme: {}'.format(x[2]), 'Datum: {}'.format(x[3]))})
        table_spec[1].update({'options': options_s})

    vals, cols = i_handler(table_spec, table)

    return vals, cols


def narudzba_menu_item_form():
    table = 'narudzba_menu_item'
    table_spec = [{'col': 'menu_item_id', 'label': 'Item', 'nullable': False, 'number': False},
                  {'col': 'kolicina', 'label': 'Kolicina', 'nullable': False, 'number': True}]

    try:
        body, header = db_conn.get_menu_item_order_name()
    except psycopg2.Error as err:
        return
    else:
        if not body:
            print('No menu item found!')
            return
        options = []
        for x in body:
            options.append({'index': x[0], 'labels': (
                'Naziv: {}'.format(x[1]), 'Opis: {}'.format(x[2]), 'Cijena: {}'.format(x[3]))})
        table_spec[0].update({'options': options})

    vals, cols = i_handler(table_spec, table)

    return vals, cols


def create_order():
    novi_stol = yn_input('Novi stol (Y/N): ')

    if novi_stol:
        stol_vals, stol_cols = stol_form()
        try:
            narudzba_vals, narudzba_cols = narudzba_form()
        except:
            return
    else:
        try:
            narudzba_vals, narudzba_cols = narudzba_form_existing_table()
        except:
            return

    narudzba_menu_item_vals_list = []

    con = True
    while con:
        try:
            narudzba_menu_item_vals, narudzba_menu_item_cols = narudzba_menu_item_form()
        except:
            return
        narudzba_menu_item_vals_list.append(narudzba_menu_item_vals)

        con = yn_input('Add another item (Y/N): ')

    if yn_input('Confirm creating order (Y/N): '):
        if novi_stol:
            db_conn.insert_order_new_table(stol_vals, stol_cols, narudzba_vals,
                                           narudzba_cols, narudzba_menu_item_vals_list, narudzba_menu_item_cols)
        else:
            db_conn.insert_order_existing_table(
                narudzba_vals, narudzba_cols, narudzba_menu_item_vals_list, narudzba_menu_item_cols)
    else:
        print('Cancelled!')


def yn_input(label):
    while True:
        x = get_lc_stpd_input(label)
        if x == 'y' or x == 'yes':
            return True
        elif x == 'n' or x == 'no':
            return False
        else:
            print('Wrong input!')


def digit_input(label):
    while True:
        x = get_lc_stpd_input(label)
        if x.isdigit():
            return x
        else:
            print('Digit input required!')


def unesi_zaposlenik():
    table = 'zaposlenik'
    table_spec = [{'col': 'oib', 'label': 'OIB', 'nullable': False, 'number': True},
                  {'col': 'ime', 'label': 'Ime', 'nullable': False, 'number': False},
                  {'col': 'prezime', 'label': 'Prezime',
                      'nullable': False, 'number': False},
                  {'col': 'kontakt', 'label': 'Kontakt',
                      'nullable': False, 'number': False},
                  {'col': 'adresa', 'label': 'Adresa',
                      'nullable': False, 'number': False},
                  {'col': 'employed', 'label': 'Zaposlen', 'nullable': False, 'number': False,
                   'options': [{'index': 't', 'labels': 'Da'}, {'index': 'f', 'labels': 'Ne'}]},
                  {'col': 'pozicija_id', 'label': 'Pozicija', 'nullable': False, 'number': False}]

    try:
        body_p, header_p = db_conn.get_pozicija()
    except psycopg2.Error as err:
        return
    else:
        if not body_p:
            print('No positions found!')
            return
        options_p = []
        for x in body_p:
            options_p.append({'index': x[0], 'labels': (
                '{}'.format(x[1]),)})
        table_spec[6].update({'options': options_p})

    vals, cols = i_handler(table_spec, table)

    if yn_input('Confirm adding employee (Y/N): '):
        try:
            db_conn.insert(table, cols, vals)
        except psycopg2.Error as err:
            print('Something went wrong!')
        else:
            print('Employee added successfully!')
    else:
        print('Cancelled!')


def unesi_pozicija():
    table = 'pozicija'
    table_spec = [{'col': 'naziv', 'label': 'Naziv',
                   'nullable': False, 'number': False}]

    vals, cols = i_handler(table_spec, table)

    if yn_input('Confirm adding position (Y/N): '):
        try:
            db_conn.insert(table, cols, vals)
        except psycopg2.Error as err:
            print('Something went wrong!')
        else:
            print('Position created successfully!')
    else:
        print('Cancelled!')


def create_stol():
    table = 'stol'
    table_spec = [{'col': 'broj_osoba', 'label': 'Broj gostiju',
                   'nullable': False, 'number': True}]

    vals, cols = i_handler(table_spec, table)

    if yn_input('Confirm adding table (Y/N): '):
        try:
            db_conn.insert(table, cols, vals)
        except psycopg2.Error as err:
            print('Something went wrong!')
        else:
            print('Stol created successfully!')
    else:
        print('Cancelled!')


def unesi_menu_item_kategorija():
    table = 'menu_item_kategorija'
    table_spec = [{'col': 'naziv', 'label': 'Naziv',
                   'nullable': False, 'number': False}]

    vals, cols = i_handler(table_spec, table)

    if yn_input('Confirm adding menu item category (Y/N): '):
        try:
            db_conn.insert(table, cols, vals)
        except psycopg2.Error as err:
            print('Something went wrong!')
        else:
            print('Menu item category created successfully!')
    else:
        print('Cancelled!')


def unesi_menu_item():
    table = 'menu_item'
    table_spec = [{'col': 'naziv', 'label': 'Naziv', 'nullable': False, 'number': False},
                  {'col': 'opis', 'label': 'Opis',
                      'nullable': False, 'number': False},
                  {'col': 'cijena', 'label': 'Cijena',
                      'nullable': False, 'number': {'type': 'numeric', 'prec': 7}},
                  {'col': 'menu_item_kategorija_id', 'label': 'Menu item kategorija', 'nullable': False, 'number': False}]

    try:
        body, header = db_conn.get_menu_item_kategorija()
    except psycopg2.Error as err:
        return
    else:
        if not body:
            print('No menu item category found!')
            return
        options = []
        for x in body:
            options.append({'index': x[0], 'labels': (
                '{}'.format(x[1]),)})
        table_spec[3].update({'options': options})

    vals, cols = i_handler(table_spec, table)

    if yn_input('Confirm adding menu item (Y/N): '):
        try:
            db_conn.insert(table, cols, vals)
        except psycopg2.Error as err:
            print('Something went wrong!')
        else:
            print('Menu item added successfully!')
    else:
        print('Cancelled!')


def search_zaposlenik(table, table_spec):

    items = ['Search employees by:', '1: Ime', '2: Prezime',
             '3: Kontakt', '4: Adresa', '5: Zaposlen', '6: Pozicija', '0: Cancel']
    o = '\n    '.join(items)
    show = True

    while True:
        if show:
            print(o)
        show = True
        x = get_lc_stpd_input('Choose index or type text: ')

        if any(v in x for v in ['1', 'ime']):
            vals, cols = i_handler([table_spec[0]], table)
        elif any(v in x for v in ['2', 'prez']):
            vals, cols = i_handler([table_spec[1]], table)
        elif any(v in x for v in ['3', 'kon']):
            vals, cols = i_handler([table_spec[2]], table)
        elif any(v in x for v in ['4', 'adre']):
            vals, cols = i_handler([table_spec[3]], table)
        elif any(v in x for v in ['5', 'zapo']):
            vals, cols = i_handler([table_spec[4]], table)
        elif any(v in x for v in ['6', 'poz']):
            vals, cols = i_handler([table_spec[5]], table)
        elif any(v in x for v in ['0', 'canc']):
            print('Cancelled!')
            return 0
        else:
            show = False
            print('Wrong input!')
            continue
        break

    try:
        body, header = db_conn.search_employee(vals, cols)
    except psycopg2.Error as err:
        raise

    return body, header


def update_zaposlenik():
    table = 'zaposlenik'
    table_spec = [{'col': 'ime', 'label': 'Ime', 'nullable': False, 'number': False},
                  {'col': 'prezime', 'label': 'Prezime',
                      'nullable': False, 'number': False},
                  {'col': 'kontakt', 'label': 'Kontakt',
                      'nullable': False, 'number': False},
                  {'col': 'adresa', 'label': 'Adresa',
                      'nullable': False, 'number': False},
                  {'col': 'employed', 'label': 'Zaposlen', 'nullable': False, 'number': False,
                   'options': [{'index': 't', 'labels': 'Da'}, {'index': 'f', 'labels': 'Ne'}]},
                  {'col': 'pozicija_id', 'label': 'Pozicija', 'nullable': False, 'number': False}]

    try:
        body_p, header_p = db_conn.get_pozicija()
    except psycopg2.Error as err:
        return
    else:
        if not body_p:
            print('No positions found!')
            return
        options_p = []
        for x in body_p:
            options_p.append(
                {'index': x[0], 'labels': ('{}'.format(x[1]),)})
        table_spec[5].update({'options': options_p})

    items = ['Options:', '1: Search for an employee',
             '2: List all', '0: Cancel']
    o = '\n    '.join(items)
    show = True

    while True:
        if show:
            print(o)
        show = True
        x = get_lc_stpd_input('Choose index or type text: ')

        if any(v in x for v in ['1', 'sear']):
            try:
                body, header = search_zaposlenik(table, table_spec)
            except psycopg2.Error as err:
                return
            else:
                if not body:
                    print('No searched employee found!')
                    return
        elif any(v in x for v in ['2', 'li', 'all']):
            try:
                body, header = db_conn.get_zaposlenik()
            except psycopg2.Error as err:
                return
            else:
                if not body:
                    print('No employee found!')
                    return
        elif any(v in x for v in ['0', 'canc']):
            print('Cancelled!')
            return
        else:
            show = False
            print('Wrong input!')
            continue
        break

    options = []
    for x in body:
        options.append({'index': x[0], 'labels': (
            'OIB: {}'.format(x[0]), 'Ime: {}'.format(x[1]), 'Prezime: {}'.format(x[2]), 'Kontakt: {}'.format(x[3]), 'Adresa: {}'.format(x[4]), 'Zaposlen: {}'.format(x[5]), 'Pozicija: {}'.format(x[6]))})

    label = create_options_view(options)
    r, v = input_handler(label, False, True, options)

    items = ['Change:', '1: Ime', '2: Prezime',
             '3: Kontakt', '4: Adresa', '5: Zaposlen', '6: Pozicija', '7: All Data', '0: Cancel']
    o = '\n    '.join(items)
    show = True

    while True:
        if show:
            print(o)
        show = True
        x = get_lc_stpd_input('Choose index or type text: ')

        if any(v in x for v in ['1', 'ime']):
            vals, cols = i_handler([table_spec[0]], table)
        elif any(v in x for v in ['2', 'prez']):
            vals, cols = i_handler([table_spec[1]], table)
        elif any(v in x for v in ['3', 'kon']):
            vals, cols = i_handler([table_spec[2]], table)
        elif any(v in x for v in ['4', 'adre']):
            vals, cols = i_handler([table_spec[3]], table)
        elif any(v in x for v in ['5', 'zapo']):
            vals, cols = i_handler([table_spec[4]], table)
        elif any(v in x for v in ['6', 'poz']):
            vals, cols = i_handler([table_spec[5]], table)
        elif any(v in x for v in ['7', 'all']):
            vals, cols = i_handler(table_spec, table)
        elif any(v in x for v in ['0', 'canc']):
            print('Cancelled!')
            return
        else:
            show = False
            print('Wrong input!')
            continue
        break

    if yn_input("Confirm updating employee's data (Y/N): "):
        try:
            db_conn.update_table(table, cols, vals, 'oib', r)
        except psycopg2.Error as err:
            print("Failed to update employee's data!")
            return
        else:
            print("Employee's data successfully updated!")
    else:
        print('Cancelled!')


def update_menu_item():
    table = 'menu_item'

    try:
        body, header = db_conn.get_menu_item()
    except psycopg2.Error as err:
        return
    else:
        if not body:
            print('No menu items found!')
            return
        options = []
        for x in body:
            options.append({'index': x[0], 'labels': (
                'Naziv: {}'.format(x[1]), 'Opis: {}'.format(x[2]), 'Cijena: {}'.format(x[3]), 'Kategorija: {}'.format(x[4]))})

    label = create_options_view(options)
    r, v = input_handler(label, False, True, options)

    table_spec = [{'col': 'naziv', 'label': 'Naziv', 'nullable': False, 'number': False},
                  {'col': 'opis', 'label': 'Opis',
                      'nullable': False, 'number': False},
                  {'col': 'cijena', 'label': 'Cijena', 'nullable': False,
                      'number': {'type': 'numeric', 'prec': 7}},
                  {'col': 'menu_item_kategorija_id', 'label': 'Kategorija', 'nullable': False, 'number': False}]

    try:
        body_k, header_k = db_conn.get_menu_item_kategorija()
    except psycopg2.Error as err:
        return
    else:
        if not body_k:
            print('No menu item category found!')
            return
        options_k = []
        for x in body_k:
            options_k.append(
                {'index': x[0], 'labels': ('{}'.format(x[1]),)})
        table_spec[3].update({'options': options_k})

    items = ['Change:', '1: Naziv', '2: Opis',
             '3: Cijena', '4: Kategorija', '5: All Data', '0: Cancel']
    o = '\n    '.join(items)
    show = True

    while True:
        if show:
            print(o)
        show = True
        x = get_lc_stpd_input('Choose index or type text: ')

        if any(v in x for v in ['1', 'naz']):
            vals, cols = i_handler([table_spec[0]], table)
        elif any(v in x for v in ['2', 'opi']):
            vals, cols = i_handler([table_spec[1]], table)
        elif any(v in x for v in ['3', 'cij']):
            vals, cols = i_handler([table_spec[2]], table)
        elif any(v in x for v in ['4', 'kate']):
            vals, cols = i_handler([table_spec[3]], table)
        elif any(v in x for v in ['5', 'all']):
            vals, cols = i_handler(table_spec, table)
        elif any(v in x for v in ['0', 'canc']):
            print('Cancelled!')
            return
        else:
            show = False
            print('Wrong input!')
            continue
        break

    if yn_input("Confirm updating menu item's data (Y/N): "):
        try:
            db_conn.update_table(table, cols, vals, 'id', r)
        except psycopg2.Error as err:
            print("Failed to update menu item's data!")
            return
        else:
            print("Menu item's data successfully updated!")
    else:
        print('Cancelled!')


def main_menu():
    items = ['Options:', '1: Unesi', '2: Promijeni', '3: Ispisi', '0: Exit']
    o = '\n    '.join(items)
    show = True

    while True:
        if show:
            print(o)
        show = True
        x = get_lc_stpd_input('Choose index or type text: ')

        if any(v in x for v in ['1', 'une']):
            insert_menu()
        elif any(v in x for v in ['2', 'pro']):
            update_menu()
        elif any(v in x for v in ['3', 'isp']):
            list_menu()
        elif any(v in x for v in ['4', 'exi']):
            print('Exit!')
            break
        else:
            show = False
            print('Wrong input!')


def insert_menu():
    items = ['Unesi:', '1: Stol', '2: Narudzbu', '3: Zaposlenika',
             '4: Poziciju zaposlenika', '5: Menu item', '6: Kategoriju menu itema', '0: Back']
    o = '\n    '.join(items)
    show = True

    while True:
        if show:
            print(o)
        show = True
        x = get_lc_stpd_input('Choose index or type text: ')

        if any(v in x for v in ['1', 'sto']):
            create_stol()
        elif any(v in x for v in ['2', 'nar']):
            create_order()
        elif any(v in x for v in ['3', 'zap']):
            unesi_zaposlenik()
        elif any(v in x for v in ['4', 'poz']):
            unesi_pozicija()
        elif any(v in x for v in ['5', 'men', 'ite']):
            unesi_menu_item()
        elif any(v in x for v in ['6', 'kat']):
            unesi_menu_item_kategorija()
        elif any(v in x for v in ['0', 'bac']):
            break
        else:
            show = False
            print('Wrong input!')


def update_menu():
    items = ['Promijeni:', '1: Podatke zaposlenika',
             '2: Podatke menu itema', '0: Back']
    o = '\n    '.join(items)
    show = True

    while True:
        if show:
            print(o)
        show = True
        x = get_lc_stpd_input('Choose index or type text: ')

        if any(v in x for v in ['1', 'zap']):
            update_zaposlenik()
        elif any(v in x for v in ['2', 'ite', 'menu']):
            update_menu_item()
        elif any(v in x for v in ['0', 'bac']):
            break
        else:
            show = False
            print('Wrong input!')


def list_menu():
    items = ['Ispisi:', '1: Zaposlenike', '2: Narudzbe stola',
             '3: Stolove posljednjih 24h', '4: Pozicije zaposlenika', '0: Back']
    o = '\n    '.join(items)
    show = True

    while True:
        if show:
            print(o)
        show = True
        x = get_lc_stpd_input('Choose index or type text: ')

        if any(v in x for v in ['1', 'zap']):
            print_zaposlenik()
        elif any(v in x for v in ['2', 'nar']):
            print_stol_narudzbe()
        elif any(v in x for v in ['3', 'sto', 'posl', '24']):
            print_stol_order_last_24h()
        elif any(v in x for v in ['4', 'poz']):
            print_pozicija()
        elif any(v in x for v in ['0', 'bac']):
            break
        else:
            show = False
            print('Wrong input!')


if __name__ == '__main__':
    db_conn = DatabaseConnection()

    # db_conn.create_restaurant_tables()
    # db_conn.populate_restaurant_tables()

    main_menu()
