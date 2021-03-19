CREATE TABLE restoran
(
    naziv varchar(25) NOT NULL,
    adresa varchar(50) NOT NULL,
    kontakt varchar(50) NOT NULL,
    radno_vrijeme varchar(50) NOT NULL,
    CONSTRAINT restoran_pk PRIMARY KEY (naziv)
);
CREATE TABLE pozicija
(
    id serial NOT NULL,
    naziv varchar(15) NOT NULL,
    CONSTRAINT pozicija_pk PRIMARY KEY (id)
);
CREATE TABLE zaposlenik
(
    oib varchar(11) NOT NULL CHECK (length(oib) = 11) ,
    ime varchar(20) NOT NULL,
    prezime varchar(20) NOT NULL,
    kontakt varchar(30) NOT NULL,
    adresa varchar(50) NOT NULL,
    zaposlen bool DEFAULT 't' NOT NULL,
    pozicija_id int NOT NULL REFERENCES pozicija (id),
    CONSTRAINT zaposlenik_pk PRIMARY KEY (oib)
);
CREATE TABLE stol
(
    id serial NOT NULL,
    broj_osoba int NOT NULL,
    vrijeme_izrade timestamp(1) DEFAULT now() NOT NULL,
    CONSTRAINT stol_pk PRIMARY KEY (id)
);
CREATE TABLE narudzba
(
    id serial NOT NULL,
    zaposlenik_oib varchar(11) NOT NULL REFERENCES zaposlenik (oib),
    stol_id int NOT NULL REFERENCES stol (id),
    CONSTRAINT narudzba_pk PRIMARY KEY (id)
);
CREATE TABLE menu_item_kategorija
(
    id serial NOT NULL,
    naziv varchar(20) NOT NULL,
    CONSTRAINT menu_item_kategorija_pk PRIMARY KEY (id)
);
CREATE TABLE menu_item
(
    id serial NOT NULL,
    naziv varchar(50) NOT NULL,
    opis varchar(500) NOT NULL,
    cijena decimal(7,2) NOT NULL,
    menu_item_kategorija_id int NOT NULL REFERENCES menu_item_kategorija (id),
    CONSTRAINT menu_item_pk PRIMARY KEY (id)
);
CREATE TABLE narudzba_menu_item
(
    id serial NOT NULL,
    narudzba_id int NOT NULL REFERENCES narudzba (id),
    menu_item_id int NOT NULL REFERENCES menu_item (id),
    kolicina smallint NOT NULL,
    CONSTRAINT narudzba_menu_item_pk PRIMARY KEY (id)
);


INSERT INTO restoran
    (naziv, adresa, kontakt, radno_vrijeme)
VALUES
    ('res', 'unknown street 234', '883482482', 'randno vrijeme...');
INSERT INTO pozicija
    (naziv)
VALUES
    ('kuhar'),
    ('konobar');
INSERT INTO zaposlenik
    (oib, ime, prezime, kontakt, adresa, zaposlen, pozicija_id)
VALUES
    ('89402938411', 'Ran', 'Per', '52642', 'Something Street 54', 't', 1),
    ('23892049382', 'Harry', 'Potter',
        '57127', 'Somethadsfreet 43', 't', 2),
    ('33824028842', 'Fdk', 'Kfjkds', '9000', 'Someadft 14', 't', 2),
    ('59394900028', 'Mark', 'Bentley', '29000', 'Sometadftreet 22', 't', 1),
    ('61934802193', 'Tjsdkf', 'Tjksdf',
        '21000', 'Somethadfreet 44', 't', 2),
    ('71705410875', 'Hummer', 'Dkdf', '41400', 'Somethiadsfeet 42', 't', 2),
    ('88994728442', 'Volkswagen', 'Guy',
        '21600', 'Somethadsfreet 34', 't', 2);
INSERT INTO menu_item_kategorija
    (naziv)
VALUES
    ('jelo'),
    ('pice');
INSERT INTO menu_item
    (naziv, opis, cijena, menu_item_kategorija_id)
VALUES
    ('Lignje', 'random opis...', 50.00, 1),
    ('Pizza', 'sir, sunka...', 50.00, 1),
    ('Riba', 'random opis...', 70.00, 1),
    ('Cola', 'random opis...', 15.50, 2);


BEGIN;
    INSERT INTO stol
        (broj_osoba)
    VALUES
        (3);
    INSERT INTO narudzba
        (zaposlenik_oib, stol_id)
    VALUES
        ('33824028842', 1);
    INSERT INTO narudzba_menu_item
        (narudzba_id, menu_item_id, kolicina)
    VALUES
        (1, 4, 3);
    INSERT INTO narudzba_menu_item
        (narudzba_id, menu_item_id, kolicina)
    VALUES
        (1, 2, 3);
    INSERT INTO stol
        (broj_osoba)
    VALUES
        (4);
    INSERT INTO narudzba
        (zaposlenik_oib, stol_id)
    VALUES
        ('71705410875', 2);
    INSERT INTO narudzba_menu_item
        (narudzba_id, menu_item_id, kolicina)
    VALUES
        (2, 4, 4);
    INSERT INTO narudzba_menu_item
        (narudzba_id, menu_item_id, kolicina)
    VALUES
        (2, 2, 3);
    INSERT INTO narudzba_menu_item
        (narudzba_id, menu_item_id, kolicina)
    VALUES
        (2, 3, 1);
    INSERT INTO narudzba
        (zaposlenik_oib, stol_id)
    VALUES
        ('61934802193', 1);
    INSERT INTO narudzba_menu_item
        (narudzba_id, menu_item_id, kolicina)
    VALUES
        (3, 4, 3);
    COMMIT;