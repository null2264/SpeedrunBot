import random


class Piglin:
    """
    A very messy Piglin Barter in python
    Based on outdated piglin loot table (Version JE 1.16.1)

    Created for ziBot
    """

    # Item Weight
    _items = [
        (5, "enchanted-book"),
        (8, "iron-boots"),
        (10, "iron-nugget"),
        (10, "splash-potion-fire-res"),
        (10, "potion-fire-res"),
        (20, "quartz"),
        (20, "glowstone-dust"),
        (20, "magma-cream"),
        (20, "ender-pearl"),
        (20, "string"),
        (40, "fire-charge"),
        (40, "gravel"),
        (40, "leather"),
        (40, "nether-brick"),
        (40, "obsidian"),
        (40, "cry-obsidian"),
        (40, "soul-sand"),
    ]

    def __init__(self, gold: int = 64):
        self.items = [BarterItem(self.weighted_random(self._items)) for i in range(gold)]

    def weighted_random(self, pairs, seed=None):
        total = sum(pair[0] for pair in pairs)
        if seed:
            random.seed(seed)
        r = random.randint(1, total)
        for weight, value in pairs:
            r -= weight
            if r <= 0:
                return value

    def __str__(self):
        return ", ".join(["{}: {}".format(str(item), item.quantity) for item in self.items])


class BarterItem:
    # Item Name
    _name = {
        "enchanted-book": "Enchanted Book - Soul Speed",
        "iron-boots": "Enchanted Iron Boots - Soul Speed",
        "iron-nugget": "Iron Nuggets",
        "splash-potion-fire-res": "Splash Potion - Fire Resistance",
        "potion-fire-res": "Potion - Fire Resistance",
        "quartz": "Nether Quartz",
        "glowstone-dust": "Glowstone Dust",
        "magma-cream": "Magma Cream",
        "ender-pearl": "Ender Pearls",
        "string": "String",
        "fire-charge": "Fire Charge",
        "gravel": "Gravel",
        "leather": "Leather",
        "nether-brick": "Nether Bricks",
        "obsidian": "Obsidian",
        "cry-obsidian": "Crying Obsidian",
        "soul-sand": "Soul Sand",
    }

    # Item quantity
    _quantity = {
        "iron-nugget": (9, 36),
        "quartz": (8, 16),
        "glowstone-dust": (5, 12),
        "magma-cream": (2, 6),
        "ender-pearl": (4, 8),
        "string": (8, 24),
        "fire-charge": (1, 5),
        "gravel": (8, 16),
        "leather": (4, 10),
        "nether-brick": (4, 16),
        "cry-obsidian": (1, 3),
        "soul-sand": (4, 16),
    }

    def __init__(self, _id):
        self.id = _id
        self.name = self._name.get(_id)
        q = self._quantity.get(_id, 1)
        self.quantity = q if not isinstance(q, tuple) else random.randrange(q[0], q[1])

    def __str__(self):
        return self.name
