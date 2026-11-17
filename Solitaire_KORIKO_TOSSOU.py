# =====================================================================
#  PROJET SOLITAIRE  -  KORIKO / TOSSOU
# =====================================================================
# On a un jeu de 52 cartes : 4 familles x 13 valeurs.
#
# Les familles sont représentées directement par leur symbole :
#   "♥" = Cœur     (rouge)
#   "♦" = Carreau  (rouge)
#   "♣" = Trèfle   (blanche)
#   "♠" = Pique    (blanche)


# =====================================================================
#  IMPORTATIONS
# =====================================================================

# On importe shuffle, qui permet de mélanger les cartes du paquet
# ("battre les cartes" se dit "shuffle" en anglais).
from random import shuffle
# On importe time, qui donne l'heure actuelle en secondes :
# elle sert à mesurer la durée de la partie (le chronomètre).
from time import time


# =====================================================================
#  CONSTANTES
# =====================================================================

# ---------------------------------------------------------------------
#  Couleurs (codes ANSI)
# ---------------------------------------------------------------------
ROUGE_VIF = "\033[91m"   # texte rouge vif  -> cartes ♥ et ♦
BLANC = "\033[97m"       # texte blanc      -> cartes ♣ et ♠ (le noir serait invisible
                         #                     sur la console sombre de PyCharm)
RESET = "\033[0m"        # retour à la couleur normale (à mettre APRÈS chaque carte)

# ---------------------------------------------------------------------
#  Familles, clavier et lettres
# ---------------------------------------------------------------------
FAMILLES = "♥♦♣♠"        # les 4 familles
FAMILLES_ROUGES = "♥♦"   # les familles rouges (sert pour les règles ET l'affichage)
# Ce que tape le joueur pour désigner une fondation -> son symbole
# c = cœur, k = carreau, t = trèfle, p = pique
Fondations_au_Clavier = {"fc": "♥", "fk": "♦", "ft": "♣", "fp": "♠"}
# Texte à afficher pour les valeurs qui ne sont pas des chiffres
LETTRES = {1: "A", 11: "J", 12: "Q", 13: "K"}

# ---------------------------------------------------------------------
#  Barème du score (inspiré du Solitaire de Windows)
# ---------------------------------------------------------------------
POINTS_FONDATION = 10            # une carte va en fondation
POINTS_DEFAUSSE_COLONNE = 5      # une carte passe de la défausse à une colonne
POINTS_CARTE_RETOURNEE = 5       # une carte cachée est retournée dans une colonne
POINTS_RETOUR_FONDATION = -15    # une carte est reprise d'une fondation
POINTS_RECYCLAGE = -100          # la défausse est remise dans la pioche

# ---------------------------------------------------------------------
#  Niveaux de jeu
# ---------------------------------------------------------------------
# Pour chaque niveau : combien de fois on peut utiliser chaque commande.
# None veut dire "illimité".
NIVEAUX = {
    "facile":    {"aide": None, "annuler": None, "resoudre": None},
    "difficile": {"aide": 5,    "annuler": 5,    "resoudre": 5},
}


# =====================================================================
#  SOUS-PROGRAMMES
# =====================================================================

# ---------------------------------------------------------------------
#  1. Construire le paquet
# ---------------------------------------------------------------------
def creer_paquet():
    """Renvoie la liste des 52 cartes, mélangée."""
    paquet = []
    for famille in FAMILLES:
        for valeur in range(1, 14):          # de 1 à 13
            paquet.append((famille, valeur))  # la valeur reste un Nombre
    # shuffle mélange la liste "sur place"
    shuffle(paquet)
    return paquet


# ---------------------------------------------------------------------
#  2. Couleur et texte d'une carte
# ---------------------------------------------------------------------
def est_rouge(carte):
    """Renvoie True si la carte est rouge (♥ ou ♦), False si elle est noire.
    Servira aussi pour la règle des colonnes (alterner rouge et noir)."""
    famille, valeur = carte             # on cherche la famille de la carte
    return famille in FAMILLES_ROUGES   # on vérifie si cette famille fait partie des familles qui doivent être rouge


def carte_en_texte(carte):
    """Renvoie le texte coloré d'une carte visible, par ex. 'Q♥' en rouge vif.
    Le texte fait toujours 3 caractères pour que les colonnes restent alignées."""
    famille, valeur = carte
    # La valeur en texte : une lettre pour 1, 11, 12, 13, sinon le nombre
    if valeur in LETTRES:
        texte = LETTRES[valeur] + famille
    else:
        texte = str(valeur) + famille
    # .ljust complète le texte avec des espaces à droite jusqu'à ce qu'il fasse 3 caractères.
    # Largeur fixe de 3 ("10♥" fait 3 caractères, "Q♥" en fait 2).
    # On le fait avant d'ajouter la couleur, car les codes ANSI comptent
    # aussi comme des caractères et fausseraient la largeur.
    texte = texte.ljust(3)
    if est_rouge(carte):
        return ROUGE_VIF + texte + RESET # on fait reset pour ramener à la couleur normale
    else:
        return BLANC + texte + RESET


# ---------------------------------------------------------------------
#  3. Distribuer les colonnes et les cartes cachées
# ---------------------------------------------------------------------
def construire_colonnes(paquet):
    colonnes = {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: []}
    # Le but c'est de faire des tours sur ces 7 colonnes en leur donnant une carte à chaque tour,mais à chaque nouveau
    # tour on commence une colonne plus loin :
    # tour 1 -> colonnes 1 à 7, tour 2 -> colonnes 2 à 7, etc. Ainsi la colonne n reçoit n cartes.
    for tour in range(1, 8):
        for colonne in range(tour, 8):
            colonnes[colonne].append(paquet.pop())  # on ajoute la dernière carte du paquet à chaque colonne
    return colonnes


def construire_nb_cachees():
    nb_cachees = {}
    # La colonne i contient i cartes au départ, et seule la dernière est visible,
    # donc elle a i - 1 cartes cachées.
    for i in range(1, 8):
        nb_cachees[i] = i - 1
    return nb_cachees


# ---------------------------------------------------------------------
#  4. Afficher le plateau (moins de 20 x 60)
# ---------------------------------------------------------------------
# Hauteur du plateau :
# renvoie le plus grand nombre de cartes visibles parmi les 7 colonnes
# c'est le nombre de lignes du plateau, puisqu'on n'affiche plus les cartes cachees
# au debut de la partie c'est 1 (chaque colonne a une seule carte visible),
# mais ca change pendant le jeu, donc on recalcule a chaque affichage
def longueur_max_colonne(colonnes,nb_cachees):
    hauteur = 0                         #on part de hauteur=0
    for colonne in colonnes:
        if len(colonnes[colonne]) - nb_cachees[colonne] > hauteur:   # plus de visibles que la hauteur actuelle ?
            hauteur = len(colonnes[colonne]) - nb_cachees[colonne]   # alors elle devient la nouvelle hauteur
    return hauteur


# Affichage des 7 colonnes :
# on affiche 3 choses :
#   1. les titres C1 a C7
#   2. une seule ligne avec le nombre de cartes cachees de chaque colonne (ex : 3X)
#   3. le plateau, ligne par ligne, avec seulement les cartes visibles
# chaque case fait 3 caracteres + le meme end, pour que les colonnes restent alignees
def afficher_plateau(colonnes, nb_cachees):
    # nombre de lignes du plateau = la colonne qui a le plus de cartes visibles
    hauteur = longueur_max_colonne(colonnes,nb_cachees)
    # 1. titres des colonnes
    for colonne in colonnes:
        print("C" + str(colonne) + " ", end=" ")  # "C1 " : 3 caracteres, comme une carte
    print()  # on passe a la ligne
    # 2. nombre de cartes cachees : "3X " si la colonne en a, sinon une case vide
    for colonne in colonnes:
        if nb_cachees[colonne] != 0:
            print(str(nb_cachees[colonne]) + "X ", end = " ")
        else:
           print("   ", end = " ")
    print()  # on passe a la ligne avant le plateau
    # 3. le plateau : seulement les cartes visibles
    for ligne in range(hauteur):
        for colonne in colonnes:
            # les cartes cachees sont au debut de la liste, les visibles viennent apres
            # donc la carte de cette ligne est a la position : nb de cachees + ligne
            position = nb_cachees[colonne] + ligne
            # pas de carte a cette position (colonne trop courte) donc case vide
            # ce test est fait en premier, sinon on lirait une carte qui n'existe pas
            if len(colonnes[colonne]) <= position:
                print("   ", end=" ")
            # sinon on affiche la carte en couleur
            else:
                print(carte_en_texte(colonnes[colonne][position]), end=" ")
        print()  # les 7 cases sont affichees : on passe à la ligne suivante

# ---------------------------------------------------------------------
#  5. Pioche et défausse
# ---------------------------------------------------------------------
# pioche   : les 24 cartes restantes après la distribution, face cachée.
# defausse : les cartes piochées, face visible. Seule la carte du dessus
#            (la dernière de la liste) peut être jouée.
# c'est la liste où se trouve la carte qui décide si on l'affiche cachée (pioche) ou visible (défausse).
# Ces listes sont créées dans nouvelle_partie.

# Piocher une carte :
# - S'il reste des cartes dans la pioche : on prend celle du dessus
#   (pop) et on la pose sur la défausse (append). Une seule carte par appel.
# - Si la pioche est vide : on remet toutes les cartes de la défausse dans la pioche une par une jusqu'à ce que la défausse soit vide.
#   Les reprendre une par une avec pop() remet automatiquement les cartes dans le bon ordre.
# - Si la pioche et la défausse sont vides : il n'y a plus rien à piocher, on prévient le joueur.
# pop() et append() modifient directement les listes de la partie.
def piocher(pioche, defausse):
    # Cas 1 : il reste des cartes dans la pioche donc on en retourne une
    if len(pioche) > 0:
        defausse.append(pioche.pop())
    # Cas 2 : la pioche est vide mais pas la défausse donc on retourne le tas
    elif len(defausse) > 0:
        while len(defausse) > 0:
            pioche.append(defausse.pop())
        print("La défausse est remise dans la pioche.")
    # Cas 3 : tout est vide donc plus rien à piocher
    else:
        print("Plus aucune carte à piocher.")

# Ligne du haut du jeu : pioche, défausse et les 4 fondations.
# Pioche   : "XX" s'il reste des cartes, des espaces si elle est vide.
# Défausse : sa carte du dessus en couleur, des espaces si elle est vide.
# chaque case fait 3 caracteres + le meme end, pour que tout reste aligne
def afficher_pioche_defausse_fondations(pioche, defausse, fondations):
    # pioche : on montre XX s'il reste des cartes (elles sont cachees), sinon du vide
    if len(pioche) > 0:
        print("XX ", end=" ")
    else:
        print("   ", end=" ")
    # defausse : on montre seulement la carte du dessus en couleur
    if len(defausse) > 0:
        print(carte_en_texte(defausse[-1]), end=" ")
    else:
        print("   ", end=" ")
    # quelques espaces pour séparer la defausse des fondations
    print(end="  ")
    # fondations : on parcourt les 4 familles si la fondation a des cartes on montre celle du dessus, sinon --
    # pour que le joueur voie quand meme où sont les fondations
    for famille in fondations:
        if len(fondations[famille]) > 0:
            print(carte_en_texte(fondations[famille][-1]), end=" ")
        else:
            print("-- ", end=" ")
    print("")


# ---------------------------------------------------------------------
#  6. Compteurs : coups, score et temps
# ---------------------------------------------------------------------
def nouveaux_compteurs(niveau):
    """Renvoie les compteurs d'une nouvelle partie :
    0 coup, 0 point, l'heure de début pour calculer le temps, et le niveau choisi.
    Le niveau est rangé ici car compteurs va déjà partout (boucle, saisie, sauvegarde) ;
    il n'est pas affiché : afficher_compteurs ne montre que coups, score et temps."""
    return {"coups": 0, "score": 0, "debut": time(), "niveau": niveau}


def points_du_coup(origine, destination, fondations):
    """Renvoie le nombre de points gagnés (ou perdus) par un coup."""
    # Vers une fondation : on se rapproche de la victoire
    if destination == "fondation":
        return POINTS_FONDATION
    # De la défausse vers une colonne : on fait avancer la pioche
    elif origine == "defausse":
        return POINTS_DEFAUSSE_COLONNE
    # D'une fondation vers une colonne : on recule
    elif origine in fondations:
        return POINTS_RETOUR_FONDATION
    # Une colonne vers une autre colonne : pas de points
    return 0


def afficher_compteurs(compteurs):
    """Affiche le nombre de coups, le score et le temps écoulé."""
    secondes = int(time() - compteurs["debut"])       # temps écoulé depuis le début
    minutes = secondes // 60
    reste = secondes % 60
    if reste < 10:
        texte_reste = "0" + str(reste) # affichage des secondes toujours en deux chifres ex: 3:05
    else:
        texte_reste = str(reste)
    print("Coups :", compteurs["coups"], "  Score :", compteurs["score"],
          "  Temps :", str(minutes) + ":" + texte_reste)


# ---------------------------------------------------------------------
#  7. Règles du jeu (répondent True ou False, ne déplacent rien)
# ---------------------------------------------------------------------
def couleurs_opposees(carte1, carte2):
    """Renvoie True si les deux cartes sont de couleurs différentes
    (une rouge et une blanche), False si elles sont de la même couleur."""
    # est_rouge donne True ou False pour chaque carte : si les deux réponses sont différentes les couleurs sont opposées.
    return est_rouge(carte1) != est_rouge(carte2)


def peut_aller_colonne(carte, colonne):
    """Renvoie True si on a le droit de poser 'carte' en bas de 'colonne'."""
    # Cas 1 : la colonne est vide ici seul un Roi (valeur 13) peut y aller.
    if len(colonne) == 0:
        return carte[1] == 13
    # Cas 2 : la colonne contient des cartes donc on compare avec la dernière
    bas = colonne[-1]
    # Il faut une couleur opposée ET une valeur juste en dessous
    return couleurs_opposees(bas, carte) and bas[1] - carte[1] == 1


def peut_aller_fondation(carte, fondation):
    """Renvoie True si on a le droit de poser 'carte' sur 'fondation'."""
    # Cas 1 : la fondation est vide ici seul un As (valeur 1) peut la commencer.
    # On teste ce cas en premier car fondation[-1] planterait sur une liste vide.
    if len(fondation) == 0:
        return carte[1] == 1
    # Cas 2 : la fondation contient des cartes donc on compare avec celle du dessus
    dessus = fondation[-1]
    # Il faut la même famille ET une valeur juste au-dessus de celle du dessus
    return carte[0] == dessus[0] and carte[1] - dessus[1] == 1


def suite_deplacable(colonnes, nb_cachees, numero, debut):
    """Renvoie True si on peut déplacer les cartes de la colonne 'numero'
    depuis la position 'debut' jusqu'en bas, False sinon."""
    colonne = colonnes[numero]
    cachees = nb_cachees[numero]
    # 1. On ne peut pas couper dans les cartes cachées (positions 0 à cachees - 1)
    if debut < cachees:
        return False
    # 2. On ne peut pas couper après la dernière carte : il n'y aurait rien à prendre
    if debut >= len(colonne):
        return False
    # 3. Chaque carte et celle juste en dessous doivent être bien rangées.
    #    La boucle s'arrête à l'avant-dernière carte (la dernière n'a rien en dessous).
    for k in range(debut, len(colonne) - 1):
        carte_dessus = colonne[k]
        carte_dessous = colonne[k + 1]
        # Les deux cartes doivent être de couleurs opposées (rouge / blanche)
        if not couleurs_opposees(carte_dessus, carte_dessous):
            return False
        # La carte du dessous doit valoir exactement 1 de moins
        if carte_dessus[1] - carte_dessous[1] != 1:
            return False
    # 4. Si on arrive ici, aucune paire n'a posé problème donc la suite de cartes est déplaçable.
    return True


# ---------------------------------------------------------------------
#  8. Vérifier un coup puis le jouer
# ---------------------------------------------------------------------
def retourner_si_besoin(colonnes, nb_cachees):
    """Après un déplacement : si une colonne ne contient plus que des cartes
    cachées, on retourne sa dernière carte (elle devient visible)."""
    # On regarde chaque colonne de 1 à 7.
    for n in range(1, 8):
        # Si la colonne n'est pas vide ET que toutes ses cartes sont cachées (autant de cartes cachées que de cartes dans la colonne)
        if len(colonnes[n]) > 0 and nb_cachees[n] == len(colonnes[n]):
            # on enlève 1 au nombre de cachées : la dernière carte devient visible.
            nb_cachees[n] = nb_cachees[n] - 1


def est_coup_valide(colonnes, nb_cachees, defausse, fondations, origine, nb_cartes, destination):
    """Renvoie "" si le coup est permis, sinon un message d'erreur. Ne modifie rien.
    origine     : "defausse", un numéro de colonne (1 à 7) ou le symbole d'une fondation
    nb_cartes   : combien de cartes on déplace
    destination : "fondation" ou un numéro de colonne (1 à 7)"""
    #1 : trouver la carte qui bouge
      # Cas A : la carte vient de la défausse
    if origine == "defausse":
        if len(defausse) == 0:        # la défausse est vide : rien à prendre
            return "La défausse est vide : pioche d'abord (p)."
        if nb_cartes != 1:            # on ne prend qu'une carte dans la défausse
            return "Une seule carte à la fois depuis la défausse."
        carte = defausse[-1]          # la carte du dessus de la défausse
      # Cas B : la carte vient d'une fondation
    elif origine in fondations:
        if len(fondations[origine]) == 0:   # cette fondation est vide
            return "Cette fondation est vide."
        if nb_cartes != 1:                  # on ne reprend qu'une carte
            return "Une seule carte à reprendre d'une fondation."
        if destination == "fondation":      # on ne la remet pas en fondation
            return "Cette carte est déjà en fondation."
        carte = fondations[origine][-1]     # la carte du dessus de cette fondation
      # Cas C : le paquet vient d'une colonne (origine est un numéro de 1 à 7)
    elif origine in colonnes:
        if len(colonnes[origine]) == 0:     # la colonne est vide : rien à prendre
            return "Cette colonne est vide."
        # On coupe la colonne pour garder les nb_cartes dernières cartes
        debut = len(colonnes[origine]) - nb_cartes
        # suite_deplacable vérifie : pas de carte cachée, la position existe,et le paquet est bien rangé
        if not suite_deplacable(colonnes, nb_cachees, origine, debut):
            return "Carte cachée ou suite mal rangée."
        carte = colonnes[origine][debut]    # la première carte de la suite
      # Origine inconnue : on refuse
    else:
        return "Origine inconnue : c1 à c7, d ou fc fk ft fp."
    #2 : vérifier que la carte peut aller à destination
      # Vers une fondation : celle de la famille de la carte (carte[0])
    if destination == "fondation":
        if nb_cartes != 1:            # une seule carte à la fois vers une fondation
            return "Une seule carte à la fois vers une fondation."
        # on demande si la carte peut aller sur sa fondation.
        if not peut_aller_fondation(carte, fondations[carte[0]]):
            return "Fondation : même famille, de l'As au Roi."
        return ""                     # tout est bon : texte vide = coup permis

      # Vers une colonne (destination est un numéro de 1 à 7)
    elif destination in colonnes:
        if destination == origine:    # on ne pose pas une colonne sur elle-même
            return "Origine et destination identiques."
        # colonne vide : seul un Roi peut y aller
        if len(colonnes[destination]) == 0 and carte[1] != 13:
            return "Seul un Roi peut aller sur une colonne vide."
        # on demande à la règle si la carte peut aller sur cette colonne.
        if not peut_aller_colonne(carte, colonnes[destination]):
            return "Sur une colonne : couleur opposée, 1 de moins."
        return ""                     # tout est bon : texte vide = coup permis

      # Destination inconnue : on refuse
    else:
        return "Destination inconnue : c1 à c7 ou f."


def coup_permis(colonnes, nb_cachees, defausse, fondations, origine, nb_cartes, destination):
    """Renvoie True si le coup est permis, False sinon (sans message).
    Sert quand on a seulement besoin de savoir oui ou non."""
    # Le coup est permis quand est_coup_valide ne renvoie aucun message (texte vide)
    return est_coup_valide(colonnes, nb_cachees, defausse, fondations, origine, nb_cartes, destination) == ""


def deplacer_cartes(colonnes, nb_cachees, defausse, fondations, origine, nb_cartes, destination):
    """Déplace les cartes. On suppose que le coup a déjà été vérifié par est_coup_valide :
    cette fonction ne vérifie rien, elle modifie directement les zones du jeu."""
    #1 : retirer les cartes de l'origine et les ranger dans une liste "cartes"
    if origine == "defausse":
        cartes = [defausse.pop()]
    # Depuis une fondation : on retire la carte du dessus de cette fondation
    elif origine in fondations:
        cartes = [fondations[origine].pop()]
    # Depuis une colonne : on coupe la colonne à la position debut
    else:
        debut = len(colonnes[origine]) - nb_cartes
        cartes = colonnes[origine][debut:]     # on prend les cartes de debut jusqu'en bas
        colonnes[origine] = colonnes[origine][:debut]      # puis on remplace la colonne par son début
    #2 : poser les cartes sur la destination
    # Vers une fondation : une seule carte, dans la fondation de sa famille
    if destination == "fondation":
        carte = cartes[0]                      # la seule carte déplacée
        fondations[carte[0]].append(carte)     # carte[0] = sa famille
    # Vers une colonne : on ajoute toutes les cartes à la fin, dans le même ordre
    else:
        colonnes[destination] = colonnes[destination] + cartes
    #3 : si une colonne n'a plus que des cartes cachées, on retourne la dernière
    retourner_si_besoin(colonnes, nb_cachees)


def jouer_coup(colonnes, nb_cachees, defausse, fondations, compteurs, origine, nb_cartes, destination):
    """Joue le coup s'il est permis, et met à jour le nombre de coups et le score.
    Renvoie "" si le coup a été joué, sinon le message d'erreur (et rien ne bouge)."""
    # 1. On vérifie le coup : on récupère le message ("" si tout est bon)
    message = est_coup_valide(colonnes, nb_cachees, defausse, fondations, origine, nb_cartes, destination)
    # 2. S'il y a un message, le coup est refusé : on le renvoie sans rien déplacer (et sans compter)
    if message != "":
        return message
    # 3. On retient combien de cartes sont cachées AVANT le coup
    cachees_avant = sum(nb_cachees.values())
    # 4. On déplace les cartes
    deplacer_cartes(colonnes, nb_cachees, defausse, fondations, origine, nb_cartes, destination)
    # 5. Un coup de plus, et les points de ce coup
    compteurs["coups"] = compteurs["coups"] + 1
    compteurs["score"] = compteurs["score"] + points_du_coup(origine, destination, fondations)
    # 6. S'il y a moins de cartes cachées qu'avant, une carte a été retournée : bonus
    if sum(nb_cachees.values()) < cachees_avant:
        compteurs["score"] = compteurs["score"] + POINTS_CARTE_RETOURNEE
    return ""


# ---------------------------------------------------------------------
#  9. Comprendre ce que le joueur tape
# ---------------------------------------------------------------------
def comprendre_colonne(mot):
    """Traduit un mot comme "c3" en numéro de colonne (3). Renvoie None si le mot n'est pas une colonne valable."""
    # Le mot doit faire 2 caractères : un "c" puis un chiffre (il n'y a que 7 colonnes)
    # isdecimal et pas isdigit : "²".isdigit() répond True, mais int("²") plante
    if len(mot) == 2 and mot[0] == "c" and mot[1].isdecimal():
        numero = int(mot[1])           # on transforme le chiffre en nombre
        if 1 <= numero <= 7:           # le numéro doit exister (colonnes 1 à 7)
            return numero
    # Dans tous les autres cas : ce n'est pas une colonne valable
    return None


def comprendre_origine(mot):
    """Traduit le 1er mot tapé par le joueur en origine du coup.
    Renvoie "defausse", un numéro de colonne, un symbole de fondation, ou None."""
    # 1. Le joueur a tapé "d" : la carte vient de la défausse
    if mot == "d":
        return "defausse"
    # 2. Le joueur a tapé "fc", "fk", "ft" ou "fp" : la carte vient d'une fondation.
    #    On cherche si le mot est une clé du dictionnaire Fondations_au_Clavier, puis on renvoie le symbole de la famille.
    elif mot in Fondations_au_Clavier:
        return Fondations_au_Clavier[mot]
    # 3. Sinon, c'est peut-être une colonne : comprendre_colonne répond.
    else:
        return comprendre_colonne(mot)


def comprendre_destination(mot):
    """Traduit le 2e mot tapé par le joueur en destination du coup.
    Renvoie "fondation", un numéro de colonne, ou None."""
    # 1. Le joueur a tapé "f" : la carte va en fondation ie celle de la famille de la carte,
    if mot == "f":
        return "fondation"
    # 2. Sinon, c'est peut-être une colonne : comprendre_colonne répond.
    else:
        return comprendre_colonne(mot)


# ---------------------------------------------------------------------
#  10. Afficher les règles et les commandes
# ---------------------------------------------------------------------
def commandes_pour_jouer():
    """Affiche comment écrire une commande.
    Utilisée dans le menu (règles et commandes) ET avec "?" pendant la partie."""
    print("----------------- COMMANDES -----------------")
    print("p             piocher une carte")
    print("ORIGINE DESTINATION     déplacer une carte")
    print("ORIGINE DESTINATION N   déplacer N cartes")
    print("ORIGINE (d'où part la carte) :")
    print("  d           la défausse")
    print("  c1 à c7     une colonne")
    print("  fc fk ft fp une fondation (♥ ♦ ♣ ♠)")
    print("DESTINATION (où va la carte) :")
    print("  f           la fondation de sa famille")
    print("  c1 à c7     une colonne")
    print("Exemples :    d c4   c5 f   c2 c6 3   fc c3")
    print("u             annuler le dernier coup")
    print("resoudre      ranger en fondation ce qui peut y aller")
    print("aide          voir les coups possibles")
    print("auto          l'ordinateur joue seul")
    print("s             sauvegarder la partie")
    print("q             quitter la partie")
    # Pause : sans elle, les commandes + le plateau (ou le menu) dépassent 20 lignes
    input("Appuie sur Entrée pour revenir...")


def afficher_regles_et_commandes():
    """Affiche les règles du Solitaire, puis les commandes.
    Utilisée dans le menu principal (choix 3)."""
    print("------------------- LES RÈGLES ------------------")
    # Le but du jeu
    print("But : ranger les 52 cartes dans les 4 fondations,")
    print("une par famille, de l'As au Roi.")
    # Les colonnes
    print("Colonnes : on pose une carte sur une carte de")
    print("valeur juste au-dessus et de couleur opposée")
    print("(exemple : 7♥ sur 8♠).")
    print("Seul un Roi peut aller sur une colonne vide.")
    print("On peut déplacer plusieurs cartes bien rangées.")
    # Les fondations
    print("Fondations : même famille, dans l'ordre")
    print("A, 2, 3... jusqu'au Roi.")
    # La pioche
    print("Pioche : p retourne une carte sur la défausse.")
    print("Quand la pioche est vide, la défausse y revient.")
    # La fin de partie
    print("Fin : quand tout est visible et qu'il n'y a plus")
    print("rien à piocher, tape resoudre pour tout ranger.")
    # Pause : règles + commandes dépassent 20 lignes, on les montre en 2 écrans
    input("Appuie sur Entrée pour voir les commandes...")
    # Puis les commandes
    commandes_pour_jouer()


# ---------------------------------------------------------------------
#  11. Exécuter la commande du joueur
# ---------------------------------------------------------------------
def traiter_la_saisie(texte, colonnes, nb_cachees, pioche, defausse, fondations,compteurs):
    """Comprend la commande tapée par le joueur et l'exécute.
    Affiche un message clair si la commande est fausse ou le coup refusé."""

    # 1. On met tout en minuscules, puis on coupe aux espaces pour avoir une liste de mots.
    mots=texte.lower().split()
    # 2. Rien tapé (le joueur a juste appuyé sur Entrée) : la liste de mots est vide.
    if len(mots) == 0:
        print("Taper une commande pour un coup.")
        return
    # 3. Commande "p" : on pioche avec la fonction piocher, puis on s'arrête
    if mots == ["p"]:
        # Si la pioche est vide et la défausse non : piocher va recycler donc pénalité
        if len(pioche) == 0 and len(defausse) > 0:
            compteurs["score"] = compteurs["score"] + POINTS_RECYCLAGE
        piocher(pioche, defausse)
        return
    # 4. Commande "?" : on affiche comment écrire les commandes, puis on s'arrête
    if mots == ["?"]:
        commandes_pour_jouer()
        return
    # 5. Commande "resoudre" : envoie en fondation toutes les cartes qui peuvent y aller.
    #    Le nombre d'utilisations est contrôlé dans boucle_de_jeu (5 au niveau difficile).
    if mots == ["resoudre"]:
        ranger_automatiquement(colonnes, nb_cachees, defausse, fondations, compteurs)
        return
    # 6. Commande "aide" : affiche les coups possibles
    if mots == ["aide"]:
        afficher_aide(colonnes, nb_cachees, defausse, fondations)
        return
    # 7. Commande "auto" : l'ordinateur joue à partir de la position actuelle
    if mots == ["auto"]:
        ordinateur_joue_seul(colonnes, nb_cachees, pioche, defausse, fondations, compteurs)
        return
    # 8. Un déplacement s'écrit avec 2 mots (origine destination) ou 3 mots (origine destination nombre de cartes) : sinon on ne comprend pas
    if len(mots) < 2 or len(mots) > 3:
        print("Commande inconnue : tape ? pour voir les commandes.")
        return
    # 9. On traduit le 1er mot : d'où part la carte ?
    #    comprendre_origine renvoie "defausse", un numéro de colonne, un symbole de fondation, ou None.
    origine = comprendre_origine(mots[0])
    if origine is None:
        print("Origine inconnue : d, c1 à c7, ou fc fk ft fp.")
        return
    # 10. On traduit le 2e mot : où va la carte ?
    #    comprendre_destination renvoie "fondation", un numéro de colonne, ou None
    destination = comprendre_destination(mots[1])
    if destination is None:
        print("Destination inconnue : f (fondation) ou c1 à c7 (colonne).")
        return
    # 11. Le nombre de cartes : 1 sauf si le joueur a tapé un 3e mot.
    #    Le 3e mot doit être fait de chiffres et plus grand que 0.
    nb_cartes = 1
    if len(mots) == 3:
        if not (mots[2].isdecimal() and int(mots[2])>0):
            print("Nombre de cartes : un entier (exemple : c2 c6 3).")
            return
        nb_cartes = int(mots[2])                 # on transforme le texte "3" en nombre 3
    # 12. On joue le coup avec jouer_coup (qui compte aussi le coup et le score) :
    #    elle renvoie "" si le coup a été joué, sinon la raison du refus, qu'on affiche
    message = jouer_coup(colonnes, nb_cachees, defausse, fondations, compteurs, origine, nb_cartes, destination)
    if message != "":
        print("Coup refusé :", message)


# ---------------------------------------------------------------------
#  12. Détecter la victoire
# ---------------------------------------------------------------------
def partie_gagnee(pioche, defausse, fondations, nb_cachees):
    """Renvoie True si la partie est gagnée, False sinon. Gagné si les 52 cartes sont en fondation, ou si la victoire est certaine :
    plus rien à piocher et plus aucune carte cachée (demande du prof)."""
    # 1. Victoire classique : on compte les cartes des 4 fondations
    total = 0
    for famille in fondations:
        total = total + len(fondations[famille])
    if total == 52:
        return True

    # 2. Victoire anticipée  :
    # S'il reste des cartes à piocher, elles sont encore cachées : pas encore gagné
    if pioche != [] or defausse != []:
        return False
    # S'il reste une seule carte cachée dans une colonne : pas encore gagné
    for colonne in range(1, 8):
        if nb_cachees[colonne] > 0:
            return False
    # Aucune raison trouvée : tout est visible et rien à piocher, c'est gagné
    return True


# ---------------------------------------------------------------------
#  13. Lancer et jouer une partie
# ---------------------------------------------------------------------
def nouvelle_partie(niveau):
    """Prépare une partie toute neuve.
    Renvoie, dans cet ordre : colonnes, nb_cachees, pioche, defausse, fondations, compteurs."""
    paquet = creer_paquet()
    colonnes = construire_colonnes(paquet)
    pioche = paquet  # les 24 cartes qui restent forment la pioche
    nb_cachees = construire_nb_cachees()
    defausse = []  # vide au début : rien n'a été pioché
    fondations = {"♥": [], "♦": [], "♣": [], "♠": []}  # une pile par famille, vides au début
    compteurs = nouveaux_compteurs(niveau)          # le niveau choisi dans le menu
    return colonnes, nb_cachees, pioche, defausse, fondations, compteurs


def utilisation_permise(commande, niveau, utilisations):
    """Renvoie True si on peut encore utiliser la commande ("aide", "annuler"
    ou "resoudre") à ce niveau, et compte cette utilisation. Sinon renvoie False."""
    limite = NIVEAUX[niveau][commande]
    # None = illimité : toujours permis, rien à compter
    if limite is None:
        return True
    # la limite est atteinte : on refuse
    if utilisations[commande] >= limite:
        print(commande, ": plus possible au niveau", niveau + ".")      # ex : "aide : plus possible..."
        return False
    # encore permis : on compte cette utilisation et on dit combien il en reste
    utilisations[commande] = utilisations[commande] + 1
    print(commande, ": il en reste", limite - utilisations[commande], "sur", limite)   # ex : "aide : il en reste 4 sur 5"
    return True


def boucle_de_jeu(colonnes, nb_cachees, pioche, defausse, fondations, compteurs):
    """Fait tourner la partie : afficher, demander une commande, l'exécuter,
    vérifier la victoire, et recommencer, jusqu'à ce que le joueur quitte ou gagne."""
    # La liste des copies du jeu, une par commande qui a changé quelque chose.
    historique = []
    # Combien de fois le joueur a utilisé chaque commande limitée (niveau difficile).
    utilisations = {"aide": 0, "annuler": 0, "resoudre": 0}
    while True:
        # 1. On affiche le score, la ligne du haut, puis le plateau
        afficher_compteurs(compteurs)
        afficher_pioche_defausse_fondations(pioche, defausse, fondations)
        afficher_plateau(colonnes, nb_cachees)
        # 2. On demande une commande au joueur
        texte = input("Commande (?, aide, s sauver, u annuler, q quitter) : ")
        mots = texte.lower().split()
        # 3. Le joueur veut quitter : on sort de la boucle
        if mots == ["q"]:
            print("Au revoir !")
            break
        # 4. Le joueur veut annuler : on reprend la dernière copie de l'historique
        if mots == ["u"]:
            if historique == []:                      # aucune copie : rien à annuler
                print("Rien à annuler.")
            # on vérifie qu'il reste des annulations (5 au niveau difficile)
            elif utilisation_permise("annuler", compteurs["niveau"], utilisations):
                colonnes, nb_cachees, pioche, defausse, fondations, compteurs = historique.pop()
            continue                                  # retour au début du while ;le plateau se réaffiche
        # Le joueur veut sauvegarder : on écrit la partie dans le fichier, puis on lui demande
        # s'il continue ou s'il revient au menu (il reprendra avec le choix 2 "Reprendre la partie").
        if mots == ["s"]:
            sauvegarder("sauvegarde.txt", colonnes, nb_cachees, pioche, defausse, fondations, compteurs)
            reponse = input("Entrée = continuer, q = revenir au menu : ")
            if reponse.lower().strip() == "q":
                print("Reprends ta partie avec le choix 2 du menu.")
                break
            continue                                  # on continue la partie
        if mots == ["aide"] or mots == ["auto"]:
            if not utilisation_permise("aide", compteurs["niveau"], utilisations):
                continue                              # refusé : on n'exécute pas la commande
        # resoudre en fin de partie ne compte pas : il faut toujours pouvoir finir
        if mots == ["resoudre"] and not partie_gagnee(pioche, defausse, fondations, nb_cachees):
            if not utilisation_permise("resoudre", compteurs["niveau"], utilisations):
                continue
        # 5. On fait une copie du jeu avant la commande, puis on exécute la commande
        avant = copie_jeu(colonnes, nb_cachees, pioche, defausse, fondations, compteurs)
        traiter_la_saisie(texte, colonnes, nb_cachees, pioche, defausse, fondations, compteurs)
        # 6. Contrôle : le jeu doit toujours avoir 52 cartes (sinon une fonction a un bug)
        if compter_cartes(colonnes, pioche, defausse, fondations) != 52:
            print("ATTENTION : des cartes ont été perdues ou dupliquées !")
        # 7. Si la commande a changé le jeu, on garde la copie d'avant dans l'historique
        if copie_jeu(colonnes, nb_cachees, pioche, defausse, fondations, compteurs) != avant:
            historique.append(avant)
        # 8. Fin de partie
        total = 0
        for famille in fondations:
            total = total + len(fondations[famille])  # nombre de cartes de cette fondation
        if total == 52:                               # tout est rangé : vraie victoire
            afficher_plateau(colonnes, nb_cachees)
            print("Bravo, partie gagnée !")
            afficher_compteurs(compteurs)
            break
        elif partie_gagnee(pioche, defausse, fondations, nb_cachees):  # victoire assurée, pas encore rangée
            print("Victoire assurée : tape resoudre pour tout ranger.")
            # pas de break ici : sinon le joueur ne pourrait pas taper resoudre


# ---------------------------------------------------------------------
#  14. Contrôle : toujours 52 cartes
# ---------------------------------------------------------------------
def compter_cartes(colonnes, pioche, defausse, fondations):
    """Compte toutes les cartes du jeu. Le total doit toujours valoir 52 :
    sinon, une fonction perd ou duplique des cartes."""
    total = len(pioche) + len(defausse)
    for famille in fondations:
        total = total + len(fondations[famille])
    for n in range(1, 8):
        total = total + len(colonnes[n])
    return total


# ---------------------------------------------------------------------
#  15. Ranger automatiquement en fin de partie (resoudre)
# ---------------------------------------------------------------------
def ranger_automatiquement(colonnes, nb_cachees, defausse, fondations, compteurs):
    """Commande resoudre : envoie en fondation, une par une, toutes les cartes
    qui ont le droit d'y aller (bas des colonnes et dessus de la défausse),
    en recommençant tant qu'une carte a pu partir."""
    carte_a_bouger = True                         # vrai au départ pour entrer dans la boucle
    while carte_a_bouger == True:
        carte_a_bouger = False                    # nouveau tour : rien n'a encore bougé
        # la carte du bas de chaque colonne (comme si le joueur tapait "cn f")
        for n in range(1, 8):
            if colonnes[n] != []:
                if jouer_coup(colonnes, nb_cachees, defausse, fondations, compteurs, n, 1, "fondation") == "":
                    carte_a_bouger = True         # une carte est partie : il faudra refaire un tour
        # la carte du dessus de la défausse (comme "d f")
        if defausse != []:
            if jouer_coup(colonnes, nb_cachees, defausse, fondations, compteurs, "defausse", 1, "fondation") == "":
                carte_a_bouger = True


# ---------------------------------------------------------------------
#  16. Annuler le dernier coup (u)
# ---------------------------------------------------------------------
def copie_jeu(colonnes, nb_cachees, pioche, defausse, fondations, compteurs):
    """Renvoie une copie de toutes les zones, dans le même ordre que nouvelle_partie.
    Il faut de vraies copies (list, dict) : sinon la copie serait la même liste
    que celle du jeu, et elle changerait en même temps que lui."""
    # Dictionnaires de listes : on copie chaque liste une par une
    copie_colonnes = {}
    for n in range(1, 8):
        copie_colonnes[n] = list(colonnes[n])
    copie_fondations = {}
    for famille in fondations:
        copie_fondations[famille] = list(fondations[famille])
    return copie_colonnes, dict(nb_cachees), list(pioche), list(defausse), copie_fondations, dict(compteurs)


# ---------------------------------------------------------------------
#  17. Aide : coups possibles et meilleur coup
# ---------------------------------------------------------------------
def coups_possibles(colonnes, nb_cachees, defausse, fondations):
    """Renvoie la liste de tous les coups permis, au format
    (origine, nb_cartes, destination). N'affiche rien.
    Sert à l'aide et à l'ordinateur qui joue seul."""
    coups = []
    destinations_possibles = [1, 2, 3, 4, 5, 6, 7, "fondation"]
    # 1. Depuis chaque colonne : 1 carte, puis 2... jusqu'à toutes les visibles
    for origine in range(1, 8):
        nb_carte_visible = len(colonnes[origine]) - nb_cachees[origine]
        for nb_cartes in range(1, nb_carte_visible + 1):
            for destination in destinations_possibles:
                if coup_permis(colonnes, nb_cachees, defausse, fondations, origine, nb_cartes, destination):
                    coups.append((origine, nb_cartes, destination))          # ex : (5, 1, 7)
    # 2. Depuis la défausse : toujours 1 carte (si elle est vide, coup_permis refuse)
    for destination in destinations_possibles:
        if coup_permis(colonnes, nb_cachees, defausse, fondations, "defausse", 1, destination):
            coups.append(("defausse", 1, destination))                      # ex : ("defausse", 1, 4)
    return coups


def coup_en_texte(coup):
    """Traduit un coup en ce que le joueur tape :
    (5, 1, 7) -> "c5 c7"   ("defausse", 1, "fondation") -> "d f"   (2, 3, 6) -> "c2 c6 3" """
    origine, nb_cartes, destination = coup
    if origine == "defausse":
        texte = "d"
    else:
        texte = "c" + str(origine)
    # avec un espace devant : traiter_la_saisie a besoin de mots séparés
    if destination == "fondation":
        texte = texte + " f"
    else:
        texte = texte + " c" + str(destination)
    if nb_cartes > 1:                             # 1 est la valeur par défaut
        texte = texte + " " + str(nb_cartes)
    return texte


def afficher_aide(colonnes, nb_cachees, defausse, fondations):
    """Affiche tous les coups possibles et le meilleur (commande aide).
    Ne déplace aucune carte."""
    coups = coups_possibles(colonnes, nb_cachees, defausse, fondations)
    if coups == []:
        print("Aucun coup possible : pioche avec p.")
    else:
        print("Coups possibles :")
        for coup in coups:
            print("  ", coup_en_texte(coup))
        meilleur = meilleur_coup(coups, colonnes, nb_cachees)
        # None = tous les coups ont la note 0 (permis mais ils ne font rien avancer)
        if meilleur is None:
            print("Conseil : aucun coup utile, pioche avec p.")
        else:
            print("Conseil :", coup_en_texte(meilleur))
    # Pause : sinon la liste + le plateau peuvent dépasser 20 lignes
    input("Appuie sur Entrée pour revenir au jeu...")


def note_du_coup(coup, colonnes, nb_cachees):
    """Renvoie la note d'un coup : plus elle est grande, plus le coup est utile.
    0 = coup inutile. Les points s'additionnent."""
    origine, nb_cartes, destination = coup
    note = 0
    if destination == "fondation":                   # une carte de plus rangée
        note = note + 3
    if origine == "defausse":
        if destination != "fondation":               # libère une carte de la pioche
            note = note + 2
    else:
        debut = len(colonnes[origine]) - nb_cartes
        if debut == nb_cachees[origine]:             # on prend toutes les cartes visibles
            if nb_cachees[origine] > 0:              # on découvre une carte cachée
                note = note + 4
            elif colonnes[origine][0][1] != 13:      # on vide la colonne (inutile pour un Roi)
                note = note + 1
    return note


def meilleur_coup(coups, colonnes, nb_cachees):
    """Renvoie le coup qui a la meilleure note, ou None si aucun coup n'est utile.
    Même méthode que longueur_max_colonne : on garde le record."""
    meilleur = None
    meilleure_note = 0       # un coup de note 0 ne sera jamais retenu
    for coup in coups:
        note = note_du_coup(coup, colonnes, nb_cachees)
        if note > meilleure_note:
            meilleure_note = note
            meilleur = coup
    return meilleur


# ---------------------------------------------------------------------
#  18. L'ordinateur joue seul (auto)
# ---------------------------------------------------------------------
def ordinateur_joue_seul(colonnes, nb_cachees, pioche, defausse, fondations, compteurs):
    """L'ordinateur joue à partir de la position actuelle, coup par coup,
    jusqu'à gagner, être bloqué, ou jusqu'à ce que le joueur tape q.
    Il ne joue que des coups utiles (note > 0), donc il ne tourne jamais en rond."""
    pioches_sans_coup = 0          # pioches d'affilée sans jouer de coup
    while True:
        # 1. Gagné : on range tout (boucle_de_jeu affichera "Bravo")
        if partie_gagnee(pioche, defausse, fondations, nb_cachees):
            ranger_automatiquement(colonnes, nb_cachees, defausse, fondations, compteurs)
            return
        # 2. Bloqué : il a vu toutes les cartes de la pioche sans rien pouvoir jouer
        if pioches_sans_coup > len(pioche) + len(defausse):
            print("L'ordinateur est bloqué : plus aucun coup utile.")
            return
        # 3. On choisit le meilleur coup
        coups = coups_possibles(colonnes, nb_cachees, defausse, fondations)
        coup = meilleur_coup(coups, colonnes, nb_cachees)
        if coup is None:
            # aucun coup utile : on pioche (traiter_la_saisie gère aussi la pénalité de recyclage)
            traiter_la_saisie("p", colonnes, nb_cachees, pioche, defausse, fondations, compteurs)
            print("L'ordinateur pioche.")
            pioches_sans_coup = pioches_sans_coup + 1
        else:
            origine, nb_cartes, destination = coup
            jouer_coup(colonnes, nb_cachees, defausse, fondations, compteurs, origine, nb_cartes, destination)
            print("L'ordinateur joue :", coup_en_texte(coup))
            pioches_sans_coup = 0
        # 4. On montre le plateau et on attend (moins de 20 lignes)
        afficher_compteurs(compteurs)
        afficher_pioche_defausse_fondations(pioche, defausse, fondations)
        afficher_plateau(colonnes, nb_cachees)
        reponse = input("Entrée = coup suivant, q = arrêter : ")
        if reponse.lower().strip() == "q":
            return


# ---------------------------------------------------------------------
#  19. Sauvegarder et reprendre une partie (s)
# ---------------------------------------------------------------------
# Un fichier texte ne contient que du texte : une carte y est écrite collée (ex : ♥12).
# Le fichier a 15 lignes, toujours dans le même ordre :
#   lignes 1 à 7   : les 7 colonnes
#   ligne 8        : le nombre de cartes cachées de chaque colonne
#   lignes 9 et 10 : la pioche, puis la défausse
#   lignes 11 à 14 : les fondations, dans l'ordre ♥ ♦ ♣ ♠
#   ligne 15       : coups, score, secondes déjà jouées, niveau
def carte_vers_mot(carte):
    """('♥', 12) -> "♥12" (sans couleurs, contrairement à carte_en_texte)."""
    return carte[0] + str(carte[1])


def mot_vers_carte(mot):
    """"♥12" -> ('♥', 12)."""
    # mot[1:] et pas mot[1] : sinon "12" deviendrait "1"
    return mot[0] , int(mot[1:])


def liste_vers_ligne(liste):
    """[('♥', 9), ('♠', 8)] -> "♥9 ♠8 " (une liste vide donne une ligne vide)."""
    ligne =""
    for carte in liste:
        ligne = ligne + carte_vers_mot(carte) + " "
    return ligne


def ligne_vers_liste(ligne):
    """"♥9 ♠8" -> [('♥', 9), ('♠', 8)] (une ligne vide donne une liste vide)."""
    liste =[]
    mots = ligne.split()                      # split enlève aussi le "\n" de la fin
    for mot in mots:
        liste.append(mot_vers_carte(mot))
    return liste


def sauvegarder(nom_fichier,colonnes,nb_cachees,pioche,defausse,fondations,compteurs):
    """Écrit toute la partie dans le fichier (commande s)."""
    # "w" efface l'ancienne sauvegarde ; utf-8 pour garder les symboles ♥♦♣♠
    fichier = open(nom_fichier, "w", encoding = "utf-8")
    # lignes 1 à 7 : les colonnes
    for colonne in colonnes:
        fichier.write(liste_vers_ligne(colonnes[colonne]) + "\n")
    # ligne 8 : les 7 nombres de cartes cachées
    for colonne in nb_cachees:
        fichier.write(str(nb_cachees[colonne]) + " " )
    fichier.write("\n")
    # lignes 9 et 10 : pioche puis défausse
    fichier.write(liste_vers_ligne(pioche) + "\n")
    fichier.write(liste_vers_ligne(defausse) + "\n")
    # lignes 11 à 14 : les fondations
    for famille in FAMILLES:
        fichier.write(liste_vers_ligne(fondations[famille]) + "\n")
    # ligne 15 : le temps déjà joué et pas l'heure de début
    # (sinon, en reprenant le lendemain, le chrono compterait toute la nuit)
    secondes = int(time() - compteurs["debut"])
    fichier.write(str(compteurs["coups"]) + " " +  str(compteurs["score"]) + " " + str(secondes) + " " + compteurs["niveau"] + "\n")
    fichier.close()
    print("partie sauvegardée")


def charger(nom_fichier):
    """Relit le fichier et renvoie, comme nouvelle_partie :
    colonnes, nb_cachees, pioche, defausse, fondations, compteurs."""
    colonnes = {}
    nb_cachees = {}
    fondations = {}
    compteurs = {}
    # readline lit une ligne à chaque appel : on relit dans le même ordre que sauvegarder
    fichier = open(nom_fichier, "r", encoding = "utf-8")
    # lignes 1 à 7 : les colonnes
    for i in range(1,8):
        colonnes[i] = ligne_vers_liste(fichier.readline())
    # ligne 8 : la colonne i est à la position i-1 de la liste
    liste = fichier.readline().split()
    for i in range(1,8):
        nb_cachees[i] = int(liste[i-1])
    # lignes 9 et 10 : pioche puis défausse
    pioche = ligne_vers_liste(fichier.readline())
    defausse = ligne_vers_liste(fichier.readline())
    # lignes 11 à 14 : les fondations
    for famille in FAMILLES:
        fondations[famille] = ligne_vers_liste(fichier.readline())
    # ligne 15 : coups, score, secondes déjà jouées, niveau
    morceaux = fichier.readline().split()
    compteurs = {
        "coups": int(morceaux[0]),
        "score": int(morceaux[1]),
        "debut": time() - int(morceaux[2]),   # le chrono reprend là où il s'était arrêté
        "niveau": morceaux[3],
    }
    fichier.close()
    return colonnes, nb_cachees, pioche, defausse, fondations, compteurs


def sauvegarde_existe(nom_fichier):
    """Renvoie True si le fichier de sauvegarde existe, False sinon
    (sans ce test, "Reprendre la partie" planterait s'il n'y a jamais eu de sauvegarde)."""
    # try : on essaie d'ouvrir le fichier ; s'il n'existe pas, Python déclenche
    # l'erreur FileNotFoundError et, au lieu de planter, passe dans except.
    try:
        fichier = open(nom_fichier, "r", encoding="utf-8")
        fichier.close()
        return True
    except FileNotFoundError:
        return False


# ---------------------------------------------------------------------
#  20. Menu principal
# ---------------------------------------------------------------------
def choisir_niveau(niveau):
    """Affiche les niveaux et renvoie celui que le joueur choisit.
    Si la réponse n'existe pas, on garde l'ancien niveau."""
    print("Niveau actuel :", niveau)
    print("1. Facile    : aide, annulations et resoudre illimités")
    print("2. Difficile : 5 aides, 5 annulations, 5 resoudre")
    choix = input("Ton choix : ").strip().lower()
    if choix == "1" or choix == "facile":
        return "facile"
    elif choix == "2" or choix == "difficile":
        return "difficile"
    else:
        print("Ce choix n'existe pas : le niveau ne change pas.")
        return niveau


def menu_principal():
    """Point de départ du programme : affiche le menu, lance ce que le joueur choisit,
    et revient au menu, jusqu'à ce qu'il choisisse Quitter."""
    niveau = "facile"     # créé avant le while : sinon il redeviendrait "facile" à chaque retour au menu
    while True:
        print()
        print("===== SOLITAIRE =====")
        print("1. Nouvelle partie")
        print("2. Reprendre la partie")
        print("3. Règles et commandes")
        print("4. Paramètres (niveau : " + niveau + ")")
        print("5. Quitter")
        choix = input("Ton choix : ").strip().lower()
        if choix == "1" or choix == "nouvelle partie":
            colonnes, nb_cachees, pioche, defausse, fondations, compteurs = nouvelle_partie(niveau)
            boucle_de_jeu(colonnes, nb_cachees, pioche, defausse, fondations, compteurs)
        elif choix == "2" or choix == "reprendre la partie":
            if not sauvegarde_existe("sauvegarde.txt"):
                print("Aucune partie sauvegardée : tape s pendant une partie.")
            else:
                colonnes, nb_cachees, pioche, defausse, fondations, compteurs = charger("sauvegarde.txt")
                boucle_de_jeu(colonnes, nb_cachees, pioche, defausse, fondations, compteurs)
        elif choix == "3" or choix == "règles et commandes":
            afficher_regles_et_commandes()
        elif choix == "4" or choix == "paramètres":
            niveau = choisir_niveau(niveau)
        elif choix == "5" or choix == "quitter":
            print("À bientôt !")
            break
        else:
            print("Ce choix n'existe pas : tape un chiffre de 1 à 5.")


# =====================================================================
#  PROGRAMME PRINCIPAL
# =====================================================================
menu_principal()

