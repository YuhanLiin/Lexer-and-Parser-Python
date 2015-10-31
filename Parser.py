from collections import deque
from Lexer import *

#########################################################################################################################
#Grammar: Consists of a dictionary of left-side symbols mapped to lists of rules for faster access
#
#Grammar rule structure: [ equivalent token , [ token1, token2 ...], [tree name], tree process, antilookahead ]
#                        Terminals are lower case, non-terminals are first letter uppercase strings
#                        S -> A b     ['S',['A','b'],'start',lambda a: a[0]+a[1]]
#                        Make rules with rule() procedure
#                        Anti-lookaheads signify before which tokens the rule DOESN'T apply. Used to set precedence.
#Parse tree: -Parse state keeps list of tokens collected by a parsing state when it shifts. [0] is name of tree.
#            -A lambda function, declared in the rules, takes in the token list and processes it into a final tree.
#             This is done when the state goes through reduction and when the start state is outputted
#            -lambda p: (p[0],p[2]) on the rule P | a b c  ----->   (name,b.value) 
#Parse states: [ left symbol, deque[seen tokens], deque[unseen tokens], origin position, token list, process, antilookahead]
##              S -> A . b from 3    ['S',['A'],['b'], 3, [name,A], lambda function, ['c']]



#Creates grammar rule using a string for the rewrite rule and also parameters for making a parse tree
def rule(rstring,tname,tprocess, antilookahead=[]):
    rule = []
    #Split string into terminal/nonterminals. First one is leftside of rewrite rule, the rest are right side of rewrite rule
    rstring = rstring.split()
    rule.append(rstring.pop(0))
    rule.append(rstring)
    #Add the tree name and process for future tree-making
    rule.append([tname])
    rule.append(tprocess)
    rule.append(antilookahead)
    return rule

def parse(grammar,chart,tokens,startrule):

    #Turn tree(list of tokens) into a finished parse tree segment via process(lambda function) 
    def make_tree(tree, process):
        return process(tree)

    #Append val to chart entry without repeats
    def addto(curpos, val):
        ref = val[:4]
        if ref not in reference[curpos]:
            chart[curpos].append(val)
            reference[curpos].append(ref)
            
    #Add all grammar rules to the current chart position that matches the pending non-terminal     
    def closure(grammar,chart,token,curpos):
        for rule in grammar[token]:
        #If any grammar rule's leftside equals to first unseen non-terminal
            #Create initialized parsing state. Mutable compenents are copied. Turn last two components of rule into Tree instance
            state = [rule[0],deque([]),deque(rule[1]),curpos,list(rule[2]),rule[3],rule[4]]
            addto(curpos,state)

    #Generates the next state via the current state and next element to add to the tree
    #Used in shifting and reduction
    def nextstate(state,element):
        #Create the next parsing state, copy the lists. 
        nextstate = [state[0],deque(state[1]),deque(state[2]),state[3],list(state[4]),state[5], state[6]]
        #Cut the beginning of the unseen to the end of the seen tokens
        shifted = nextstate[2].popleft()
        nextstate[1].append(shifted)

        #If element is a token, add its value. Otherwise just add it
    ##    if type(element) == Token:
    ##        nextstate[4].append(element.value)
    ##    else:
        nextstate[4].append(element)
        return nextstate
        
    #Match terminal tokens and advance the parsing state into the next chart position
    def shift(tokens,chart,state,curpos):
        #If current token matches the next token of the parsing state
        if tokens[curpos] == state[2][0]:
            #Generate the next state by modifying the current state and adding the current token to the tree
            addto(curpos+1,nextstate(state,tokens[curpos].value))

    #Complete the non-terminal of a finished parsing state and add it to the current position
    def reduction(origin,chart,equal,curpos,tree):
        #Go back to the origin chart position to look for the origin state
        for state in chart[origin]:
            #If the state isn't finished and its pending token is the desired non-terminal
            if state[2] and state[2][0] == equal:
                #Generate the next state by modifying the origin state and add to chart
                addto(curpos,nextstate(state,tree))
                
    #Create alternate version of the chart as reference to addto()
    reference = {}
    #End marker to prevent shifting outside of the token list at the end
    endline, endpos = tokens[-1].line, tokens[-1].col
    tokens.append(Token("endmarker",'eof',-1,-1,endline,endpos))
    #Initialize chart positions as lists, add the starting rule to chart[0]
    for n in xrange(len(tokens)+1):
        chart[n] = []
        reference[n] = []
    chart[0].append([startrule[0],[],deque(startrule[1]),0,startrule[2],startrule[3],startrule[4]])

    for curpos in xrange(len(tokens)+1):
        #If current postion is empty, no state has shifted successfully and the string is invalid
        if chart[curpos] == []:
            curtoken = tokens[curpos-1]
            raise Exception('Unexpected '+str(curtoken.value)+' at line '+str(curtoken.line)+' position '+str(curtoken.col)+'.')

        #For each state in the current chart position. Loop will include new states added by closure.    
        for state in chart[curpos]:
            #Variables for components of current parsing state
            equal = state[0]
            seen = state[1]
            unseen = state[2]
            origin = state[3]
            tree = state[4]
            process = state[5]
            antilookahead = state[6]

            #If we are at the end of the tokens and we have the state we started with finished, string is valid. Then the tree is returned
            if curpos == len(tokens)-1 and equal == startrule[0] and unseen == deque([]) and origin == 0:
                return make_tree(tree,process)

            #If state is finished and the next token isn't an anti-lookahead, finish its tree and run reduction to it, passing in the finished tree
            if not unseen:
                if tokens[curpos] not in antilookahead:
                    tree = make_tree(tree,process)
                    reduction(origin,chart,equal,curpos,tree)
                else:
                    continue
            #If state's pending token is non-terminal(first letter cap) then run closure
            elif unseen[0][0] >= 'A' and unseen[0][0] <= 'Z':
                closure(grammar,chart,unseen[0],curpos)                
            #If state's pending token is terminal run shifting to it
            else:
                shift(tokens,chart,state,curpos)

##############################################################################
#Test grammars and lexers
##
##                
##grammar = {'S':[rule('S S STM',None,lambda p: [p[2]]+p[1]),
##		rule('S ',None,lambda p: [])],
##	   'CALL':[rule('CALL ID OPTARG','call',lambda p: (p[0],p[1],p[2]))],
##           'ID':[rule('ID word',None,lambda p: p[1])],
##	   'OPTARG':[rule('OPTARG pl ARGS pr',None,lambda p: p[2]),
##                    rule('OPTARG pl pr',None,lambda p: [])],
##	   'ARGS':[rule('ARGS EXP comma ARGS',None,lambda p: [p[1]]+p[3]),
##                   rule('ARGS EXP',None,lambda p: [p[1]])],
##	   'EXP':[rule('EXP int','int',lambda p: (p[0],p[1])),
##                  rule('EXP EXP add EXP','add',lambda p: (p[0],p[1],p[3])),
##		  rule('EXP EXP minus EXP','minus',lambda p: (p[0],p[1],p[3])),
##		  rule('EXP CALL',None,lambda p: p[1])],
##	   'STM':[rule('STM EXP scolon','statement',lambda p: (p[0],p[1]))]}
##chart = {}       
##
##
##lexer = [temp('word','[A-Za-z]+'),
##         temp('pl','\('),
##         temp('pr','\)'),
##         temp('int','[1-9][0-9]*',lambda a: int(a)),
##         temp('comma',','),
##         temp('space',' +',lambda a: None),
##         temp('newline','\n',lambda a: None),
##         temp('add','\+'),
##         temp('scolon',';'),
##         temp('minus','\-')]
##
##string = '''proc (1+2-3,4);
##            proc (1+2-3,4);'''
##
##print parse(grammar, {}, lex(string, lexer), grammar['S'][0])

##############################################################################

