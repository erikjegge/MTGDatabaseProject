import cv2
import os
from skimage.metrics import structural_similarity as ssim
import numpy as np

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

# Example usage:
query = "resized.jpg"
candidates_folder = "./candidates"
match, score = find_best_match(query, candidates_folder)
print(f"\nBest match: {match} with SSIM score {score:.4f}")