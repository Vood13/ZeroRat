-- LocalScript
-- Поместить в StarterPlayer > StarterCharacterScripts
-- Управляет атаками, блоком и анимациями

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")

local player = Players.LocalPlayer
local character = script.Parent
local humanoid = character:WaitForChild("Humanoid")
local animator = humanoid:WaitForChild("Animator")

-- Настройки
local COMBO_TIMEOUT = 1.5 -- Время для продолжения комбо (секунды)
local PUNCH_COOLDOWN = 0.3 -- Кулдаун между ударами

-- Переменные комбо
local currentCombo = 0
local maxCombo = 4
local lastPunchTime = 0
local canPunch = true
local isBlocking = false

-- RemoteEvent для синхронизации
local attackEvent = ReplicatedStorage:WaitForChild("AttackEvent")

-- Загрузка анимаций
local function loadCharacterAnimations()
	local selectedCharacter = player:WaitForChild("SelectedCharacter").Value
	local characterFolder = ReplicatedStorage:WaitForChild("Characters"):FindFirstChild(selectedCharacter)
	
	if not characterFolder then
		warn("Персонаж не найден: " .. selectedCharacter)
		return nil
	end
	
	local animationsFolder = characterFolder:WaitForChild("Animations")
	local animations = {}
	
	-- Загружаем анимации ударов
	for i = 1, maxCombo do
		local animObject = animationsFolder:FindFirstChild("Punch" .. i)
		if animObject then
			animations["Punch" .. i] = animator:LoadAnimation(animObject)
		end
	end
	
	return animations
end

-- Загрузка общих анимаций (блок, получение урона)
local function loadSharedAnimations()
	local sharedFolder = ReplicatedStorage:WaitForChild("SharedAnimations")
	local animations = {}
	
	local blockAnim = sharedFolder:FindFirstChild("Block")
	local hitAnim = sharedFolder:FindFirstChild("Hit")
	
	if blockAnim then
		animations.Block = animator:LoadAnimation(blockAnim)
	end
	
	if hitAnim then
		animations.Hit = animator:LoadAnimation(hitAnim)
	end
	
	return animations
end

local punchAnimations = loadCharacterAnimations()
local sharedAnimations = loadSharedAnimations()

-- Функция для выполнения удара
local function performPunch()
	if not canPunch or isBlocking then
		return
	end
	
	-- Проверка таймаута комбо
	local currentTime = tick()
	if currentTime - lastPunchTime > COMBO_TIMEOUT then
		currentCombo = 0
	end
	
	-- Увеличиваем комбо
	currentCombo = currentCombo + 1
	if currentCombo > maxCombo then
		currentCombo = 1
	end
	
	-- Проигрываем анимацию
	local punchAnim = punchAnimations["Punch" .. currentCombo]
	if punchAnim then
		punchAnim:Play()
	end
	
	-- Отправляем на сервер для обработки урона
	attackEvent:FireServer("Punch", currentCombo)
	
	-- Кулдаун
	canPunch = false
	lastPunchTime = currentTime
	
	task.wait(PUNCH_COOLDOWN)
	canPunch = true
end

-- Функция для блока
local function startBlock()
	if isBlocking then return end
	
	isBlocking = true
	
	if sharedAnimations.Block then
		sharedAnimations.Block:Play()
	end
	
	-- Можно добавить эффект блока (например, уменьшение урона)
	print("Блок активирован")
end

local function stopBlock()
	if not isBlocking then return end
	
	isBlocking = false
	
	if sharedAnimations.Block then
		sharedAnimations.Block:Stop()
	end
	
	print("Блок деактивирован")
end

-- Управление
UserInputService.InputBegan:Connect(function(input, gameProcessed)
	if gameProcessed then return end
	
	-- ЛКМ - удар
	if input.UserInputType == Enum.UserInputType.MouseButton1 then
		performPunch()
	end
	
	-- F - блок
	if input.KeyCode == Enum.KeyCode.F then
		startBlock()
	end
end)

UserInputService.InputEnded:Connect(function(input, gameProcessed)
	-- Отпускание блока
	if input.KeyCode == Enum.KeyCode.F then
		stopBlock()
	end
end)

-- Обработка получения урона (вызывается сервером)
local hitEvent = ReplicatedStorage:WaitForChild("HitEvent")
hitEvent.OnClientEvent:Connect(function()
	if sharedAnimations.Hit and not isBlocking then
		sharedAnimations.Hit:Play()
	end
end)

print("Система боя загружена для персонажа: " .. player:WaitForChild("SelectedCharacter").Value)
