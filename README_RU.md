# 🥊 Roblox Fighting System - Athena Character

Система боя для твоего файтинг/баттлграунд плейса в Roblox Studio.

## 📁 Структура в Roblox Studio

### 1. ReplicatedStorage
```
ReplicatedStorage
├── Characters
│   └── Athena
│       └── Animations
│           ├── Punch1 (Animation)
│           ├── Punch2 (Animation)
│           ├── Punch3 (Animation)
│           └── Punch4 (Animation)
└── SharedAnimations
    ├── Block (Animation)
    └── Hit (Animation)
```

### 2. ServerScriptService
- **CharacterSelector.lua** - создаёт StringValue "Athena" для каждого игрока
- **CombatServer.lua** - обрабатывает урон и атаки на сервере

### 3. StarterPlayer > StarterCharacterScripts
- **CombatController.lua** - управление атаками и блоком на клиенте

## 🎮 Управление

- **ЛКМ (Left Mouse Button)** - Удар (комбо до 4 ударов)
- **F** - Блок (удерживай для защиты)

## ⚙️ Как установить

### Шаг 1: Создай структуру папок
1. В **ReplicatedStorage** создай:
   - Папку `Characters`
   - В ней папку `Athena`
   - В ней папку `Animations`
   - Папку `SharedAnimations`

2. Добавь свои Animation объекты:
   - `Punch1`, `Punch2`, `Punch3`, `Punch4` в `Characters/Athena/Animations`
   - `Block` и `Hit` в `SharedAnimations`

### Шаг 2: Добавь скрипты
1. Скопируй `CharacterSelector.lua` в **ServerScriptService**
2. Скопируй `CombatServer.lua` в **ServerScriptService**
3. Скопируй `CombatController.lua` в **StarterPlayer > StarterCharacterScripts**

### Шаг 3: Тестируй!
Запусти игру и попробуй атаковать! ЛКМ для ударов, F для блока.

## 🔧 Настройки

В `CombatController.lua`:
```lua
local COMBO_TIMEOUT = 1.5 -- Время для продолжения комбо
local PUNCH_COOLDOWN = 0.3 -- Кулдаун между ударами
```

В `CombatServer.lua`:
```lua
local PUNCH_DAMAGE = {
    [1] = 10,  -- Урон Punch1
    [2] = 12,  -- Урон Punch2
    [3] = 15,  -- Урон Punch3
    [4] = 20   -- Урон Punch4
}
local ATTACK_RANGE = 7 -- Дистанция атаки
local BLOCK_REDUCTION = 0.5 -- Уменьшение урона при блоке (50%)
```

## ✨ Особенности

- ✅ Система комбо (4 удара)
- ✅ Блокировка атак
- ✅ Автоматический поиск цели
- ✅ Защита от читеров (server-side валидация)
- ✅ Анимации через файлы (не ID)
- ✅ Легко расширяется для новых персонажей

## 🚀 Что дальше?

- Добавь новых персонажей в папку `Characters`
- Создай систему выбора персонажей в лобби
- Добавь спецатаки и ультимейты
- Создай систему здоровья и интерфейс

Удачи с разработкой! 🎮
