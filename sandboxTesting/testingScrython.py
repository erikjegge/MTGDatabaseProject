import scrython
import requests
import time
import os

IMAGE_PATH = "./candidates/"

def delete_images(folder_path):
    image_extensions = ('.jpg', '.jpeg', '.png')
    deleted_files = []

    for filename in os.listdir(folder_path):
        if filename.lower().endswith(image_extensions):
            file_path = os.path.join(folder_path, filename)
            try:
                os.remove(file_path)
                deleted_files.append(filename)
            except Exception as e:
                print(f"Failed to delete {filename}: {e}")

    print(f"Deleted {len(deleted_files)} images:")
    for f in deleted_files:
        print(f" - {f}")

def save_image(path, url, name):
    response = requests.get(url)

    with open('{}{}.png'.format(path, name), 'wb') as f:
        print('got here')
        f.write(response.content)

def load_image(path):
    image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)  # use grayscale for comparison
    return cv2.resize(image, (300, 300))  # resize for consistent comparison

def compare_images(imageA, imageB):
    score, _ = ssim(imageA, imageB, full=True)
    return score  # higher = more similar

def find_best_match(query_path, candidates_folder):
    query_image = load_image(query_path)
    best_score = -1
    best_match = None

    for filename in os.listdir(candidates_folder):
        candidate_path = os.path.join(candidates_folder, filename)
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue
        candidate_image = load_image(candidate_path)
        score = compare_images(query_image, candidate_image)
        print(f"Comparing with {filename}: SSIM = {score:.4f}")
        if score > best_score:
            best_score = score
            best_match = filename

    return best_match, best_score

#card = scrython.cards.Named(fuzzy='Peerless Samurai',set='NEO')
#print(card)
data = scrython.cards.Search(q="++{}".format('Cone of Cold'))
#counter = 0
for r in data.data():
    card = scrython.cards.Id(id=r['id'])
    save_image(IMAGE_PATH, card.image_uris(0, 'normal'), card.id())
    #counter += 1

##print(len(card))
print(card.name())
print(card.prices('usd'))
print(card.prices('usd_foil'))
print(card.type_line())
print(card.colors())
print(card.mana_cost())
print(card.id())
print(card.collector_number())
print(card.highres_image())

#save_image(IMAGE_PATH, card.image_uris(0, 'normal'), card.name())

#delete_images(IMAGE_PATH)

#card = scrython.cards.Collector(code='NEO',collector_number='96')
#print(card.id())
#print(card.name())
#print(card.prices('usd'))
#print(card.prices('usd_foil'))
#print(card.type_line())
#print(card.colors())
#print(card.mana_cost())
#print(card.id())