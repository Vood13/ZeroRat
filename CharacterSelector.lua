-- ServerScript
-- Поместить в ServerScriptService
-- Создаёт StringValue с выбранным персонажем для каждого игрока

local Players = game:GetService("Players")

Players.PlayerAdded:Connect(function(player)
	-- Создаём StringValue с именем персонажа
	local characterValue = Instance.new("StringValue")
	characterValue.Name = "SelectedCharacter"
	characterValue.Value = "Athena"
	characterValue.Parent = player
	
	print(player.Name .. " присоединился. Персонаж: Athena")
end)
