doc_encoding = {}
with open("../extract/doc_extract/doc_encoding.txt", 'r', encoding='UTF-8') as f1:
    text = f1.read()
temp = text.split('\n')
for item in temp:
    if item is '':
        continue
    temp2 = item.split('\t')
    doc_encoding[temp2[0]] = temp2[1]
print(doc_encoding)