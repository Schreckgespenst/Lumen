from ollama import chat

response = chat(
    model='gemma4',
    messages=[{'role': 'user', 'content': 'Today (April 12) I\'ve had the following for the day.  Lunch: a glass of buttermilk, 1 serve of overnight oats made of chia seeds, oats, milk, curd, honey, 1 grilled chicken sandwich made of brown multigrain bread, grilled chicken, veggies, sauces, 1 cheese slice Evening Snacks: 1 mushroom cheese omellete, 120gm chicken popcorn with ketchup'}],
)
print(response.message.content)