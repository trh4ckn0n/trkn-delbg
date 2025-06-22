# Background Removal Vidéo avec Flask

Ce projet Flask permet de retirer l’arrière-plan d’une vidéo en remplaçant le fond par une image personnalisée.  
Il utilise la bibliothèque [rembg](https://github.com/danielgatis/rembg) pour effectuer la suppression de fond avec différents modèles, et OpenCV pour le traitement vidéo.

---

## Fonctionnalités

- Upload vidéo et image de fond via une interface web simple.
- Choix parmi plusieurs modèles de suppression de fond (`u2net`, `u2netp`, `u2net_human_seg`, `u2net_cloth_seg`).
- Traitement image avec pré-traitement CLAHE (amélioration du contraste).
- Post-traitement du masque alpha (lissage et morphologie).
- Conservation de la piste audio d’origine.
- Résultat téléchargeable directement depuis l’interface.
- Style interface “hacker fluo” minimaliste.

---

## Installation

### Prérequis

- Python 3.8+
- ffmpeg (installé et accessible en ligne de commande)
- pip

### Cloner le dépôt

```bash
git clone https://github.com/trh4ckn0n/trkn-delbg.git cd trkn-delbg
```
### Installer les dépendances Python

```bash
pip install -r requirements.txt
```

> **Remarque** : Si `requirements.txt` n’est pas présent, installer manuellement :  
> `pip install flask rembg opencv-python-headless numpy`

---

## Usage

1. Lancer l’application Flask :

```bash
python app.py
```

2. Ouvrir dans le navigateur :  
[https://trkn-delbg.onrender.com](https://trkn-delbg.onrender.com) (démo en ligne)  
ou  
[http://localhost:5000](http://localhost:5000) (en local)

3. Uploader une vidéo et une image de fond, choisir un modèle, puis lancer le traitement.

4. Télécharger la vidéo traitée avec le fond modifié.

---

## Structure des fichiers

- app.py : Application Flask principale.
- templates/index.html : Template HTML pour l’interface web.
- static/output/ : Dossier où sont sauvegardées les vidéos traitées.

---

## Modèles disponibles

| Modèle           | Description                            |
|------------------|------------------------------------|
| u2net            | Modèle standard, bon pour tout usage |
| u2netp           | Modèle léger, moins précis           |
| u2net_human_seg  | Optimisé pour segmentation humaine  |
| u2net_cloth_seg  | Optimisé pour segmentation des vêtements |

---

## Remarques

- Assurez-vous que ffmpeg est installé et dans le PATH pour la gestion audio/vidéo.
- Le traitement vidéo est assez gourmand en ressources, une machine avec CPU performant est recommandée.
- La qualité du résultat dépend beaucoup du modèle choisi et de la vidéo d’entrée.

---

## Liens utiles

- Repo GitHub : https://github.com/trh4ckn0n/trkn-delbg  
- Démo en ligne : [https://trkn-delbg.onrender.com](https://trkn-delbg.onrender.com)

---

## Licence

Projet libre à usage personnel et éducatif.

---

Créé par trhacknon
