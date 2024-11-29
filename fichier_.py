import sqlalchemy
import pandas as pd
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Table, Date, MetaData
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# Configuration de la base de données
base_url = os.getenv("DATABASE_URL", "postgresql://postgres:1212@localhost:5432/postgres")
engine = create_engine(base_url)

# Définir la Base
Base = declarative_base()

# Table intermédiaire pour la relation plusieurs-à-plusieurs
Annonce_equipement = Table(
    'annonce_equipement', Base.metadata,
    Column('annonce_id', Integer, ForeignKey('annonce.annonce_id'), primary_key=True),
    Column('equipement_id', Integer, ForeignKey('equipement.equi_id'), primary_key=True)
)

# Table des villes
class Cities(Base):
    __tablename__ = 'cities'
    city_id = Column(Integer, primary_key=True)
    name_ville = Column(String, unique=True)
    latitude = Column(Float)  # Nouvelle colonne pour la latitude
    longitude = Column(Float)  # Nouvelle colonne pour la longitude

    annonces = relationship('Annonce', order_by='Annonce.annonce_id', back_populates='city')

# Table des annonces
class Annonce(Base):
    __tablename__ = 'annonce'
    annonce_id = Column(Integer, primary_key=True)
    title = Column(String)
    price = Column(Float)
    date = Column(Date)
    nb_rooms = Column(Integer)
    nb_baths = Column(Integer)
    nb_salons = Column(Integer)
    etage = Column(Integer)
    surface_area = Column(Integer)
    property = Column(String)
    link = Column(String)
    city_id = Column(Integer, ForeignKey('cities.city_id'))
    city = relationship('Cities', back_populates='annonces')

    equipements = relationship('Equipement', secondary=Annonce_equipement, back_populates='annonces')

# Table des équipements
class Equipement(Base):
    __tablename__ = 'equipement'
    equi_id = Column(Integer, primary_key=True)
    name_equi = Column(String)

    annonces = relationship('Annonce', secondary=Annonce_equipement, back_populates='equipements')

# Création des tables (si non existantes)
Base.metadata.create_all(engine)
print("Tables créées ou déjà existantes !")

# Création de la session
Session = sessionmaker(bind=engine)
session = Session()

# Lecture du fichier CSV
file_path = 'data_annonce.csv'
data = pd.read_csv(file_path, encoding='utf-8')

# Nettoyage des noms de villes
data['Localisation'] = data['Localisation'].str.strip().str.lower()

# Ajout des villes avec latitude et longitude
for _, row in data.iterrows():
    city_name = row['Localisation'].strip().lower()  # Nettoyage du nom de la ville
    latitude = row['Latitude']  # Lecture de la latitude
    longitude = row['Longitude']  # Lecture de la longitude
    
    # Rechercher la ville dans la base de données
    city = session.query(Cities).filter_by(name_ville=city_name).first()
    
    if not city:
        print(f"Ajout d'une nouvelle ville : {city_name}")
        city = Cities(name_ville=city_name, latitude=latitude, longitude=longitude)
        session.add(city)
    else:
        print(f"Mise à jour des coordonnées pour : {city_name}")
        city.latitude = latitude
        city.longitude = longitude

    # Commit des modifications
    session.commit()

print("Mise à jour des villes terminée.")

# Traitement des annonces et équipements
for _, row in data.iterrows():
    city_name = row['Localisation'].strip().lower()
    city = session.query(Cities).filter_by(name_ville=city_name).first()

    if city:
        annonce = Annonce(
            city_id=city.city_id,
            title=row['Title'],
            price=row['Price'],
            date=row['Date'],
            nb_rooms=row['Chambre'],
            nb_baths=row['Salle de bain'],
            nb_salons=row['Salons'],
            etage=row['Etage'],
            surface_area=row['Surface habitable'],
            property=row['Age de bien'],
            link=row['EquipementURL'],
        )
        session.add(annonce)

        # Ajout des équipements
        equipement_col = ['Ascenseur', 'Balcon', 'Chauffage', 'Climatisation',
                          'Concierge', 'Cuisine equipee', 'Duplex', 'Meuble', 'Parking',
                          'Securite', 'Terrasse']

        for eq_name in equipement_col:
            equipement_exists = row.get(eq_name, False)
            if equipement_exists:
                equipement = session.query(Equipement).filter_by(name_equi=eq_name).first()
                if not equipement:
                    equipement = Equipement(name_equi=eq_name)
                    session.add(equipement)

                if equipement not in annonce.equipements:
                    annonce.equipements.append(equipement)

        session.commit()

print("Traitement des annonces et équipements terminé.")
