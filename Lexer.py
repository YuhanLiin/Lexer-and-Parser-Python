import re
#Lexer takes in ordered list of token templates to generate tokens.
#Each type of token has a name, a regexp, uses a lambda function (takes matched string) to generate token.value and a corresponding mode
#To ignore a token pass in a function that returns None


#Class for tokens
class Token(object):
    #name = name of token
    #value = the data stored in this token based on the matched string
    #start/end = where the token started/ended in the string
    def __init__(self,name,value,start,end,line,col):
        self.name = name
        self.value = value
        self.start = start
        self.end = end
        self.line = line
        self.col = col

    #String equivalency
    def __eq__(self,other):
        return self.name == other
        
    #__eq__ and __hash__ must be same
    def __hash__(self):
        return hash(self.name)

    #Prints name and value
    def __repr__(self):
        return '('+self.name+', "'+str(self.value)+'"'+')'

#Class for templates of tokens        
class Token_template(object):
    #name = Name of produced token, lowercase
    #regexp = Regular expression recognizing the token
    #process = Lambda function for processing the string into the token value
    def __init__(self,name,regexp,process=None):
        self.name = name
        r = re.compile(regexp)
        self.regexp = r
        self.process = process

    #Returns first token from string [start]  
    def match(self,string,start,line,col):
        #create re.match object with string
        matched = self.regexp.match(string,start)
        #return False if nothing matches
        if not matched:
            return False
        #Keep track of where the token ends so it can be used as the start position again
        end = matched.end()
        #If the token has a process, process the value. Otherwise, keep the matched string.
        if self.process:
            value = self.process(matched.group())
        else:
            value = matched.group()
        #Look for newline chars inside string. Update col # as well
        for c in matched.group():
            if c == '\n':
                line += 1
                col = 1
        #Make a new token with extracted args if it matches correctly
        return Token(self.name,value,start,end,line,col)

#Initializes a token template
def temp(name,regexp,process=None):
    return Token_template(name,regexp,process)

#Actual lexer that takes input string and list of templates
def lex(string,lexer):
    start = 0
    tokens = []
    line = 1
    col = 1
    #If empty string is passed, hardcode return empty list
    if string == '':
        return []
    #Keep looping until no more string is left
    while True:
        valid = False

        for tp in lexer:
            #Search through every token template looking for a match
            token = tp.match(string, start, line, col)
            #Go to the next one if no match
            if not token:
                continue
            #If token matched isn't ignored, add it to the list            
            if token.value != None:
                tokens.append(token)
            #Update column, line, and start values of the lexer
            start = token.end
            valid = True
            if token.line != line:
                col = 1
            else:
                col += token.end - token.start
            line = token.line
            break
                    
        #If the last run yielded no tokens, the string is not viable
        if not valid:
            raise Exception("Token error at position "+str(col)+" on line "+str(line)+'.')
        #If we are at the end of the string, return finished list of tokens
        if start == len(string): return tokens
 

 
