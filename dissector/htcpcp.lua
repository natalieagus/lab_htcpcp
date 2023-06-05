----------------------------------------------------------------------------------------
-- Helper Functions
----------------------------------------------------------------------------------------

function split(str, delimiter, max)
	--[[
		Splits a string `str` by `delimiter`, such that the returned `table` (array) has
		a maximum of `max` strings. Set `max` to `-1` for no limit.

		This function is blatantly stolen and adapted from 
		https://gist.github.com/jaredallard/ddb152179831dd23b230.
	]]
	local result = { }
	local from  = 1
	local delim_from, delim_to = string.find( str, delimiter, from  )
	local count = 1
	while delim_from do
		if max >= -1 and count == max then
			break
		end
		table.insert( result, string.sub( str, from , delim_from-1 ) )
		from  = delim_to + 1
		delim_from, delim_to = string.find( str, delimiter, from  )
		count = count + 1
	end
	table.insert( result, string.sub( str, from  ) )
	return result
end

function trim(str)
	--[[
		Removes the trailing spaces before and after a string `str`.

		This function is blatantly stolen from https://stackoverflow.com/a/27455195/3051996.
	]]
	return str:match( "^%s*(.-)%s*$" )
end

----------------------------------------------------------------------------------------
-- Protocol Definition
----------------------------------------------------------------------------------------

local htcpcp_proto = Proto("htcpcp", "Hyper Text Coffee Pot Control Protocol")
local htcpcp_port = 5030

function htcpcp_proto.dissector(buffer, pinfo, tree)
	--[[
		Dissection Function for HTCPCP
		This is called **once** for every HTCPCP packet to process the packet.
		- `buffer`: Packet buffer, a `Tvb` object.
		- `pinfo`: Packet columns, a `Pinfo` object
		- `tree`: Tree root, a `TreeItem` object.
	]]

	local length = buffer:len()
	if length == 0 then return end

	-- Set protocol name under the Column
	pinfo.cols.protocol = htcpcp_proto.name

	-- Defines HTCPCP tree to be displayed at the bottom left of the Wireshark GUI
	local htcpcp_tree = tree:add(htcpcp_proto, buffer(), htcpcp_proto.description)
	
	-- Parse the contents of the packet
	local msg = buffer(0, length):string()
	local lines = split(msg, "\r\n\r\n", 2)         	-- a double CRLF divides the startline & headers from the HTTP body.

	local headers = split(lines[1], "[\n(\r\n)]", -1)   -- a CRLF divides the headers from each other (by right). Here, we allow for LFs too.
	local body = ""

	if #lines == 2 then
		body = body .. lines[2]                     -- Append the body portion of the message to `body`.
	end

	-- Parse the start line of the packet.
	local start_line = trim(table.remove(headers, 1))
	local start_line_tree = htcpcp_tree:add(start_line)
	local start_parts = split(start_line, " ", 3)
	local is_response = (trim(start_parts[1]) == "HTCPCP/1.1")

	if is_response then
		-- A response would be: `<Version> <Status Code> <Response Phrase>`, e.g. `HTCPCP/1.1 418 I'm a Teapot`.
		start_line_tree:add("Response Version: ", trim(start_parts[1]))
		start_line_tree:add("Status Code: ", trim(start_parts[2]))
		start_line_tree:add("Response Phrase: ", trim(start_parts[3]))
	else
		-- A request would be: `<Method> <URI> <Version>`, e.g. `GET coffee://ducky HTTP/1.1`.
		start_line_tree:add("Request Method: ", trim(start_parts[1]))
		start_line_tree:add("Request URI: ", trim(start_parts[2]))
		start_line_tree:add("Request Version: ", trim(start_parts[3]))
	end

	-- Parse the headers
	---- Ideally, we'd just add them to the Wireshark display immediately.
	---- However, this part is necessary since the HTCPCP server doesn't properly separate the HTCPCP message 
	---- body from the HTCPCP message headers with a double CRLF. 
	---- So we simply check if a header is valid (i.e. is formatted as `key: value`, where `key` consists of 
	---- alphanumeric characters or a dash). If not valid, we assume it's part of the body.
	for i, header in ipairs(headers) do
		local header_valid = false
		header = trim(header)
		if header:len() ~= 0 then
			local parts = split(header, ":", 2)
			if #parts == 2 then
				key = trim(parts[1])
				value = trim(parts[2])

				-- Only add if key is valid
				if string.find(key, "^([%d%a-]+)$") then
					htcpcp_tree:add(parts[1]..": "..parts[2])
					header_valid = true
				end
			end
			if not header_valid then
				print("Warning: Invalid header: "..header)
			end
		end

	end

	-- Defines HTCPCP Data tree to be displayed as well.
	-- Ideally, we'd pass this off to another dissector. But I'm lazy.
	if body:len() > 0 then
		local htcpcp_data_tree = tree:add("HTCPCP Data")
		htcpcp_data_tree:add(body)
	end

end

-- Add the dissector to the dissector table for Wireshark.
local tcp_table = DissectorTable.get("tcp.port")
tcp_table:add(htcpcp_port, htcpcp_proto)
