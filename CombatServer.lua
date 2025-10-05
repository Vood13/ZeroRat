-- ServerScript
-- Поместить в ServerScriptService
-- Обрабатывает атаки и урон на сервере

local ReplicatedStorage = game:GetService("ReplicatedStorage")

-- Создаём RemoteEvents
local attackEvent = Instance.new("RemoteEvent")
attackEvent.Name = "AttackEvent"
attackEvent.Parent = ReplicatedStorage

local hitEvent = Instance.new("RemoteEvent")
hitEvent.Name = "HitEvent"
hitEvent.Parent = ReplicatedStorage

-- Настройки урона
local PUNCH_DAMAGE = {
	[1] = 10, -- Punch1
	[2] = 12, -- Punch2
	[3] = 15, -- Punch3
	[4] = 20  -- Punch4 (финальный удар)
}

local ATTACK_RANGE = 7 -- Дистанция атаки
local BLOCK_REDUCTION = 0.5 -- Уменьшение урона при блоке (50%)

-- Кулдауны для защиты от читов
local playerCooldowns = {}
local COOLDOWN_TIME = 0.25

-- Функция для поиска цели перед игроком
local function findTarget(attacker)
	local character = attacker.Character
	if not character then return nil end
	
	local humanoidRootPart = character:FindFirstChild("HumanoidRootPart")
	if not humanoidRootPart then return nil end
	
	local attackerPosition = humanoidRootPart.Position
	local attackerLookVector = humanoidRootPart.CFrame.LookVector
	
	local closestTarget = nil
	local closestDistance = ATTACK_RANGE
	
	-- Ищем ближайшего врага
	for _, player in pairs(game.Players:GetPlayers()) do
		if player ~= attacker and player.Character then
			local targetHRP = player.Character:FindFirstChild("HumanoidRootPart")
			local targetHumanoid = player.Character:FindFirstChild("Humanoid")
			
			if targetHRP and targetHumanoid and targetHumanoid.Health > 0 then
				local distance = (targetHRP.Position - attackerPosition).Magnitude
				
				-- Проверяем, что цель в радиусе атаки
				if distance <= ATTACK_RANGE then
					-- Проверяем, что цель перед игроком
					local directionToTarget = (targetHRP.Position - attackerPosition).Unit
					local dotProduct = attackerLookVector:Dot(directionToTarget)
					
					if dotProduct > 0.5 and distance < closestDistance then
						closestTarget = player
						closestDistance = distance
					end
				end
			end
		end
	end
	
	return closestTarget
end

-- Проверка блока у цели
local function isTargetBlocking(target)
	-- Можно добавить атрибут или BoolValue для проверки блока
	local character = target.Character
	if not character then return false end
	
	-- Пока просто возвращаем false, можно расширить
	return false
end

-- Обработка атаки
attackEvent.OnServerEvent:Connect(function(player, attackType, comboNumber)
	-- Проверка кулдауна
	local currentTime = tick()
	if playerCooldowns[player] and currentTime - playerCooldowns[player] < COOLDOWN_TIME then
		return
	end
	playerCooldowns[player] = currentTime
	
	-- Поиск цели
	local target = findTarget(player)
	
	if target then
		local targetCharacter = target.Character
		local targetHumanoid = targetCharacter:FindFirstChild("Humanoid")
		
		if targetHumanoid and targetHumanoid.Health > 0 then
			-- Расчёт урона
			local damage = PUNCH_DAMAGE[comboNumber] or 10
			
			-- Проверка блока
			if isTargetBlocking(target) then
				damage = damage * BLOCK_REDUCTION
			end
			
			-- Наносим урон
			targetHumanoid:TakeDamage(damage)
			
			-- Отправляем событие попадания на клиент цели
			hitEvent:FireClient(target)
			
			print(player.Name .. " ударил " .. target.Name .. " на " .. damage .. " урона (Комбо: " .. comboNumber .. ")")
		end
	end
end)

print("Система боя (сервер) загружена")
