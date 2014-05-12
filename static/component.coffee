fs = require "fs"
process = require "process"
EventEmitter = require('events').EventEmitter

events = new EventEmitter()

args = process.argv.slice(2)

verboseIndex = args.indexOf("-v")
log = ->
emergencyLog = console.log

# performing verbose option
if verbose = verboseIndex >= 0
	args.splice(verboseIndex, 1)
	log = console.log	

# config
componentsDir = "../components/"
templatesDir = "../templates/components/"
templatesPath = "#{templatesDir}#{args[0]}/"
scriptsPath = "#{componentsDir}#{args[0]}/scripts/"
stylesPath = "#{componentsDir}#{args[0]}/styles/"

# actions
actions = 
	componentDir : false
	scriptsDir : false
	scriptsFile : false
	stylesDir : false
	stylesFile : false
	templatesDir : false
	templatesFile : false

checkActions = ->
	allDone = true

	for action of actions
		if !actions[action]
			allDone = false
			break

	allDone

successWithLog = (key) ->
	log "#{key}: ok"

	actions[key] = true

	if checkActions()
		emergencyLog "Component '#{args[0]}' successfully created!"

# processing
log "Performing new component '#{args[0]}'"

events.on "make-component", (name) ->
	log "Creating front-end component directory for '#{name}'..."

	# create a dir with 0777
	fs.mkdir "#{componentsDir}#{name}", ->
		successWithLog "componentDir"

		events.emit "make-scripts", name
		events.emit "make-styles", name

events.on "make-scripts", (name) ->
	log "Creating first coffee-script file for component"

	fs.mkdir scriptsPath, ->
		successWithLog "scriptsDir"

		fs.writeFile "#{scriptsPath}#{name}.coffee", "", -> successWithLog "scriptsFile"

events.on "make-styles", (name) ->
	log "Creating first stylus file for component"

	fs.mkdir stylesPath, ->
		successWithLog "stylesDir"

		fs.writeFile "#{stylesPath}#{name}.styl", "", -> successWithLog "stylesFile"

events.on "make-template-component", (name) ->
	log "Creating template component and first file"

	fs.mkdir templatesPath, ->
		successWithLog "templatesDir"

		fs.writeFile "#{templatesPath}#{name}.html", "", -> successWithLog "templatesFile"


fs.readdir "#{componentsDir}", (err, files) ->
	# create new dir in components section
	try 
		if files.indexOf(args[0]) >= 0
			throw new Error("Component '#{args[0]}' already exists!")

		events.emit "make-component", args[0]
		events.emit "make-template-component", args[0]

	catch err 
		if err instanceof TypeError
			emergencyLog "Oops! Something is wrong. Closing"

		else
			emergencyLog err

