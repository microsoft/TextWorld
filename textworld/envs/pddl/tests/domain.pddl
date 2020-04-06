;; Specification in PDDL of the Alfred domain
;; Intended to be used with Fast Downward which supports PDDL 2.2 level 1 plus the :action-costs requirement from PDDL 3.1.

(define (domain alfred)
 (:requirements
    :adl
    :action-costs
    :typing
 )
 (:types
  agent
  location
  receptacle
  object
  rtype
  otype
  )


 (:predicates
    (atLocation ?a - agent ?l - location)                     ; true if the agent is at the location
    (receptacleAtLocation ?r - receptacle ?l - location)      ; true if the receptacle is at the location (constant)
    (objectAtLocation ?o - object ?l - location)              ; true if the object is at the location
    (openable ?r - receptacle)                                ; true if a receptacle is openable
    (opened ?r - receptacle)                                  ; true if a receptacle is opened
    (inReceptacle ?o - object ?r - receptacle)                ; object ?o is in receptacle ?r
    (isReceptacleObject ?o - object)                          ; true if the object can have things put inside it
    (inReceptacleObject ?innerObject - object ?outerObject - object)                ; object ?innerObject is inside object ?outerObject
    (isReceptacleObjectFull ?o - object)                      ; true if the receptacle object contains something
    (wasInReceptacle ?o - object ?r - receptacle)             ; object ?o was or is in receptacle ?r now or some time in the past
    (checked ?r - receptacle)                                 ; whether the receptacle has been looked inside/visited
    (examined ?l - location)                                  ; TODO
    (receptacleType ?r - receptacle ?t - rtype)               ; the type of receptacle (Cabinet vs Cabinet|01|2...)
    (canContain ?rt - rtype ?ot - otype)                      ; true if receptacle can hold object
    (objectType ?o - object ?t - otype)                       ; the type of object (Apple vs Apple|01|2...)
    (holds ?a - agent ?o - object)                            ; object ?o is held by agent ?a
    (holdsAny ?a - agent)                                     ; agent ?a holds an object
    (holdsAnyReceptacleObject ?a - agent)                        ; agent ?a holds a receptacle object
    (full ?r - receptacle)                                    ; true if the receptacle has no remaining space
    (isClean ?o - object)                                     ; true if the object has been clean in sink
    (cleanable ?o - object)                                   ; true if the object can be placed in a sink
    (isHot ?o - object)                                       ; true if the object has been heated up
    (heatable ?o - object)                                    ; true if the object can be heated up in a microwave
    (isCool ?o - object)                                      ; true if the object has been cooled
    (coolable ?o - object)                                    ; true if the object can be cooled in the fridge
    (pickupable ?o - object)                                   ; true if the object can be picked up
    (moveable ?o - object)                                      ; true if the object can be moved
    (toggleable ?o - object)                                  ; true if the object can be turned on/off
    (isOn ?o - object)                                        ; true if the object is on
    (isToggled ?o - object)                                   ; true if the object has been toggled
    (sliceable ?o - object)                                   ; true if the object can be sliced
    (isSliced ?o - object)                                    ; true if the object is sliced
 )

  (:functions
    (distance ?from ?to)
    (total-cost) - number
   )

;; All actions are specified such that the final arguments are the ones used
;; for performing actions in Unity.


(:action look
    :parameters (?a - agent ?l - location)
    :precondition
        (and
            (atLocation ?a ?l)
        )
    :effect
        (and
            (checked ?l)
        )
)

(:action inventory
    :parameters (?a - agent)
    :precondition
        ()
    :effect
        (and
            (checked ?a)
        )
)

(:action examineReceptacle
    :parameters (?a - agent ?r - receptacle)
    :precondition
        (and
            (exists (?l - location)
                (and
                    (atLocation ?a ?l)
                    (receptacleAtLocation ?r ?l)
                )
            )
        )
    :effect
        (and
            (checked ?r)
        )
)

(:action examineObject
    :parameters (?a - agent ?o - object)
    :precondition
        (or
            ;(exists (?l - location)
            ;    (and
            ;        (atLocation ?a ?l)
            ;        (objectAtLocation ?o ?l)
            ;    )
            ;)
            (exists (?l - location, ?r - receptacle)
                (and
                    (atLocation ?a ?l)
                    (receptacleAtLocation ?r ?l)
                    ; (objectAtLocation ?o ?l)
                    (inReceptacle ?o ?r)
                    (or (not (openable ?r)) (opened ?r))  ; receptacle is opened if it is openable.
              )
            )
            (holds ?a ?o)
        )
    :effect
        (and
            (checked ?o)
        )
)

;; agent goes to receptacle
 (:action GotoLocation
    :parameters (?a - agent ?lStart - location ?lEnd - location ?r - receptacle)
    :precondition (and
                    (atLocation ?a ?lStart)
                    (receptacleAtLocation ?r ?lEnd)
                    ;(exists (?r - receptacle) (receptacleAtLocation ?r ?lEnd))
                  )
    :effect (and
                (not (atLocation ?a ?lStart))
                (atLocation ?a ?lEnd)
                ; (forall (?r - receptacle)
                ;     (when (and (receptacleAtLocation ?r ?lEnd)
                ;                (or (not (openable ?r)) (opened ?r)))
                ;         (checked ?r)
                ;     )
                ; )
                ; (increase (total-cost) (distance ?lStart ?lEnd))
                (increase (total-cost) 1)
            )
 )

;; agent opens receptacle
 (:action OpenObject
    :parameters (?a - agent ?l - location ?r - receptacle)
    :precondition (and
            (openable ?r)
            (atLocation ?a ?l)
            (receptacleAtLocation ?r ?l)
            (forall (?re - receptacle)
                (not (opened ?re)))
            )
    :effect (and
                (opened ?r)
                (checked ?r)
                (increase (total-cost) 1)
            )
 )
;; agent closes receptacle
 (:action CloseObject
    :parameters (?a - agent ?l - location ?r - receptacle)
    :precondition (and
            (openable ?r)
            (atLocation ?a ?l)
            (receptacleAtLocation ?r ?l)
            (opened ?r)
            )
    :effect (and
                (not (opened ?r))
                (increase (total-cost) 1)
            )

 )

 ;; agent picks up object from a receptacle
 (:action PickupObject
    :parameters (?a - agent ?l - location ?o - object ?r - receptacle)
    :precondition
        (and
            (pickupable ?o)
            (atLocation ?a ?l)
            (receptacleAtLocation ?r ?l)
            ; (objectAtLocation ?o ?l)
            (inReceptacle ?o ?r)
            (not (holdsAny ?a))  ; agent's hands are empty.
            ; (not (holdsAnyReceptacleObject ?a))
            (or (not (openable ?r)) (opened ?r))  ; receptacle is opened if it is openable.
            ; (not (isReceptacleObject ?o))
        )
    :effect
        (and
            (not (inReceptacle ?o ?r))
            (holds ?a ?o)
            (holdsAny ?a)
            (not (objectAtLocation ?o ?l))
            ;(not (full ?r))
            (increase (total-cost) 1)
        )
 )

;; agent puts down an object
 (:action PutObject
    :parameters (?a - agent ?l - location ?ot - otype ?rt - rtype ?o - object ?r - receptacle)
    :precondition (and
            (holds ?a ?o)
            (atLocation ?a ?l)
            (receptacleAtLocation ?r ?l)
            (or (not (openable ?r)) (opened ?r))    ; receptacle is opened if it is openable
            ;(not (full ?r))
            (receptacleType ?r ?rt)
            (objectType ?o ?ot)
            ;(canContain ?rt ?ot)
            ;(not (holdsAnyReceptacleObject ?a))
            )
    :effect (and
                (inReceptacle ?o ?r)
                (objectAtLocation ?o ?l)
                ;(full ?r)
                (not (holds ?a ?o))
                (not (holdsAny ?a))
                (increase (total-cost) 1)
            )
 )

;; agent cleans some object
 (:action CleanObject
    :parameters (?a - agent ?l - location ?r - receptacle ?o - object)
    :precondition (and
            (cleanable ?o)
            (or
                (receptacleType ?r SinkType)
                (receptacleType ?r SinkBasinType)
            )
            (atLocation ?a ?l)
            (receptacleAtLocation ?r ?l)
            (holds ?a ?o)
            )
    :effect (and
                (increase (total-cost) 5)
                (isClean ?o)
            )
 )


;; agent heats-up some object
 (:action HeatObject
    :parameters (?a - agent ?l - location ?r - receptacle ?o - object)
    :precondition (and
            (heatable ?o)
            (or
                (receptacleType ?r MicrowaveType)
            )
            (atLocation ?a ?l)
            (receptacleAtLocation ?r ?l)
            (holds ?a ?o)
            )
    :effect (and
                (increase (total-cost) 5)
                (isHot ?o)
                (not (isCool ?o))
            )
 )

;; agent cools some object
 (:action CoolObject
    :parameters (?a - agent ?l - location ?r - receptacle ?o - object)
    :precondition (and
            (coolable ?o)
            (or
                (receptacleType ?r FridgeType)
            )
            (atLocation ?a ?l)
            (receptacleAtLocation ?r ?l)
            (holds ?a ?o)
            )
    :effect (and
                (increase (total-cost) 5)
                (isCool ?o)
                (not (isHot ?o))
            )
 )


;; agent toggle object
 (:action ToggleObject
    :parameters (?a - agent ?l - location ?o - object)
    :precondition (and
            (toggleable ?o)
            (atLocation ?a ?l)
            (objectAtLocation ?o ?l)
            )
    :effect (and
                (increase (total-cost) 5)
                (when (isOn ?o)
                    (not (isOn ?o)))
                (when (not (isOn ?o))
                    (isOn ?o))
                (isToggled ?o)
            )
 )


;; agent slices some object with a knife
 (:action SliceObject
    :parameters (?a - agent ?l - location ?co - object ?ko - object)
    :precondition
            (and
                (sliceable ?co)
                (or
                    (objectType ?ko KnifeType)
                    (objectType ?ko ButterKnifeType)
                )
                (atLocation ?a ?l)
                (objectAtLocation ?co ?l)
                (holds ?a ?ko)
            )
    :effect (and
                (increase (total-cost) 5)
                (isSliced ?co)
            )
 )


)
