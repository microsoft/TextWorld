
(define
    (problem test_alfworld)

    (:domain alfred)

    (:objects
        agent1 - agent

        AlarmClockType - otype
        AppleType - otype
        BaseballBatType - otype
        BasketBallType - otype
        BathtubType - otype
        BlindsType - otype
        BookType - otype
        BootsType - otype
        BowlType - otype
        BoxType - otype
        BreadType - otype
        ButterKnifeType - otype
        CandleType - otype
        CDType - otype
        CellPhoneType - otype
        ChairType - otype
        ClothType - otype
        CreditCardType - otype
        CupType - otype
        CurtainsType - otype
        DeskLampType - otype
        DishSpongeType - otype
        EggType - otype
        FloorLampType - otype
        FootstoolType - otype
        ForkType - otype
        GlassbottleType - otype
        HandTowelType - otype
        HousePlantType - otype
        KettleType - otype
        KeyChainType - otype
        KnifeType - otype
        LadleType - otype
        LaptopType - otype
        LaundryHamperLidType - otype
        LettuceType - otype
        LightSwitchType - otype
        MirrorType - otype
        MugType - otype
        NewspaperType - otype
        PaintingType - otype
        PanType - otype
        PaperTowelRollType - otype
        PaperTowelType - otype
        PencilType - otype
        PenType - otype
        PepperShakerType - otype
        PillowType - otype
        PlateType - otype
        PlungerType - otype
        PosterType - otype
        PotatoType - otype
        PotType - otype
        RemoteControlType - otype
        SaltShakerType - otype
        ScrubBrushType - otype
        ShowerDoorType - otype
        ShowerGlassType - otype
        SinkType - otype
        SoapBarType - otype
        SoapBottleType - otype
        SpatulaType - otype
        SpoonType - otype
        SprayBottleType - otype
        StatueType - otype
        StoveKnobType - otype
        TeddyBearType - otype
        TelevisionType - otype
        TennisRacketType - otype
        TissueBoxType - otype
        ToiletPaperRollType - otype
        ToiletPaperType - otype
        TomatoType - otype
        TowelType - otype
        VaseType - otype
        WatchType - otype
        WateringCanType - otype
        WindowType - otype
        WineBottleType - otype

        ArmChairType - rtype
        BathtubBasinType - rtype
        BedType - rtype
        CabinetType - rtype
        CartType - rtype
        CoffeeMachineType - rtype
        CoffeeTableType - rtype
        CounterTopType - rtype
        DeskType - rtype
        DiningTableType - rtype
        DrawerType - rtype
        DresserType - rtype
        FridgeType - rtype
        GarbageCanType - rtype
        HandTowelHolderType - rtype
        LaundryHamperType - rtype
        MicrowaveType - rtype
        OttomanType - rtype
        PaintingHangerType - rtype
        SafeType - rtype
        ShelfType - rtype
        SideTableType - rtype
        SinkBasinType - rtype
        SofaType - rtype
        StoveBurnerType - rtype
        ToasterType - rtype
        ToiletPaperHangerType - rtype
        ToiletType - rtype
        TowelHolderType - rtype
        TVStandType - rtype

        AlarmClock - object
        BaseballBat - object
        BasketBall - object
        Blinds1 - object
        Blinds2 - object
        Book1 - object
        Book2 - object
        Bowl1 - object
        Bowl2 - object
        Bowl3 - object
        CD - object
        CellPhone - object
        Chair1 - object
        Chair2 - object
        CreditCard - object
        DeskLamp - object
        KeyChain - object
        Laptop - object
        LaundryHamperLid - object
        LightSwitch - object
        Mirror - object
        Mug1 - object
        Mug2 - object
        Pencil - object
        Pen - object
        Pillow1 - object
        Pillow2 - object
        Pillow3 - object
        Window1 - object
        Window2 - object

        Bed - receptacle
        Desk - receptacle
        Drawer - receptacle
        GarbageCan - receptacle
        LaundryHamper - receptacle
        Safe - receptacle
        Shelf - receptacle

        locCenter - location
        locBed - location
        locDesk - location
        locShelf - location
        locLaundryHamper - location
        locDrawer - location
        locGarbageCan - location
        locSafe - location
    )

    (:init
        (receptacleType Bed BedType)
        (receptacleType Desk DeskType)
        (receptacleType Drawer DrawerType)
        (receptacleType GarbageCan GarbageCanType)
        (receptacleType LaundryHamper LaundryHamperType)
        (receptacleType Safe SafeType)
        (receptacleType Shelf ShelfType)

        (objectType AlarmClock AlarmClockType)
        (objectType BaseballBat BaseballBatType)
        (objectType BasketBall BasketBallType)
        (objectType Blinds1 BlindsType)
        (objectType Blinds2 BlindsType)
        (objectType Book1 BookType)
        (objectType Book2 BookType)
        (objectType Bowl1 BowlType)
        (objectType Bowl2 BowlType)
        (objectType Bowl3 BowlType)
        (objectType CD CDType)
        (objectType CellPhone CellPhoneType)
        (objectType Chair1 ChairType)
        (objectType Chair2 ChairType)
        (objectType CreditCard CreditCardType)
        (objectType DeskLamp DeskLampType)
        (objectType KeyChain KeyChainType)
        (objectType Laptop LaptopType)
        (objectType LaundryHamperLid LaundryHamperLidType)
        (objectType LightSwitch LightSwitchType)
        (objectType Mirror MirrorType)
        (objectType Mug1 MugType)
        (objectType Mug2 MugType)
        (objectType Pen PenType)
        (objectType Pencil PencilType)
        (objectType Pillow1 PillowType)
        (objectType Pillow2 PillowType)
        (objectType Pillow3 PillowType)
        (objectType Window1 WindowType)
        (objectType Window2 WindowType)

        (pickupable AlarmClock)
        (pickupable BaseballBat)
        (pickupable BasketBall)
        (pickupable Book1)
        (pickupable Book2)
        (pickupable Bowl1)
        (pickupable Bowl2)
        (pickupable Bowl3)
        (pickupable CD)
        (pickupable CellPhone)
        (pickupable CreditCard)
        (pickupable KeyChain)
        (pickupable Laptop)
        (pickupable Mug1)
        (pickupable Mug2)
        (pickupable Pen)
        (pickupable Pencil)
        (pickupable Pillow1)
        (pickupable Pillow2)
        (pickupable Pillow3)

        (isReceptacleObject Bowl1)
        (isReceptacleObject Bowl2)
        (isReceptacleObject Bowl3)
        (isReceptacleObject Mug1)
        (isReceptacleObject Mug2)

        (openable Drawer)
        (openable Safe)

        (atLocation agent1 locCenter)

        (cleanable Bowl1)
        (cleanable Bowl2)
        (cleanable Bowl3)
        (cleanable Mug1)
        (cleanable Mug2)

        (heatable Mug1)
        (heatable Mug2)

        (coolable Bowl1)
        (coolable Bowl2)
        (coolable Bowl3)
        (coolable Mug1)
        (coolable Mug2)

        (toggleable DeskLamp)

        (inReceptacle AlarmClock Shelf)
        (inReceptacle Book1 Bed)
        (inReceptacle Book2 Drawer)
        (inReceptacle Bowl1 Desk)
        (inReceptacle Bowl2 Desk)
        (inReceptacle Bowl3 Shelf)
        (inReceptacle CD Desk)
        (inReceptacle CellPhone Drawer)
        (inReceptacle CreditCard Desk)
        (inReceptacle DeskLamp Desk)
        (inReceptacle KeyChain Drawer)
        (inReceptacle Laptop Desk)
        (inReceptacle Mug1 Desk)
        (inReceptacle Mug2 Shelf)
        (inReceptacle Pen Shelf)
        (inReceptacle Pencil Shelf)
        (inReceptacle Pillow1 Bed)
        (inReceptacle Pillow2 Bed)
        (inReceptacle Pillow3 Bed)

        (receptacleAtLocation Bed locBed)
        (receptacleAtLocation Desk locDesk)
        (receptacleAtLocation Drawer locDrawer)
        (receptacleAtLocation GarbageCan locGarbageCan)
        (receptacleAtLocation LaundryHamper locLaundryHamper)
        (receptacleAtLocation Safe locSafe)
        (receptacleAtLocation Shelf locShelf)

        (objectAtLocation AlarmClock locShelf)
        (objectAtLocation BaseballBat locLaundryHamper)
        (objectAtLocation BasketBall locLaundryHamper)
        (objectAtLocation Blinds1 locCenter)
        (objectAtLocation Blinds2 locCenter)
        (objectAtLocation Book1 locBed)
        (objectAtLocation Book2 locDrawer)
        (objectAtLocation Bowl1 locDesk)
        (objectAtLocation Bowl2 locDesk)
        (objectAtLocation Bowl3 locShelf)
        (objectAtLocation CD locDesk)
        (objectAtLocation CellPhone locBed)
        (objectAtLocation Chair1 locBed)
        (objectAtLocation Chair2 locDesk)
        (objectAtLocation CreditCard locDrawer)
        (objectAtLocation DeskLamp locDesk)
        (objectAtLocation KeyChain locDrawer)
        (objectAtLocation Laptop locDesk)
        (objectAtLocation LaundryHamperLid locLaundryHamper)
        (objectAtLocation LightSwitch locCenter)
        (objectAtLocation Mirror locDesk)
        (objectAtLocation Mug1 locDesk)
        (objectAtLocation Mug2 locShelf)
        (objectAtLocation Pen locShelf)
        (objectAtLocation Pencil locShelf)
        (objectAtLocation Pillow1 locBed)
        (objectAtLocation Pillow2 locBed)
        (objectAtLocation Pillow3 locBed)
        (objectAtLocation Window1 locCenter)
        (objectAtLocation Window2 locCenter)
    )

    (:goal
        (and
            (exists (?ot - object
                    ?a - agent
                    ?l - location)
                (and
                    (objectType ?ot DeskLampType)
                    (toggleable ?ot)
                    (isToggled ?ot)
                    (objectAtLocation ?ot ?l)
                    (atLocation ?a ?l)
                )
            )
            (exists (?o - object
                    ?a - agent)
                (and
                    (objectType ?o CDType)
                    (holds ?a ?o)
                )
            )
        )
    )
)
