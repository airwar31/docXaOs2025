from search_image import SIFTImageSearch

sift = SIFTImageSearch('images/')
sift.build_index()

result = sift.search_similar('images/6-15.jpg')
result2 = sift.search_similar('images/7-16.jpg')

print(result)
print(result2)