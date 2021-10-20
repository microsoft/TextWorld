tw-make tw-simple --rewards dense    --goal detailed --seed 18 --test --silent -f --output games/tw-rewardsDense_goalDetailed.z8
tw-make tw-simple --rewards balanced --goal detailed --seed 18 --test --silent -f --output games/tw-rewardsBalanced_goalDetailed.z8
tw-make tw-simple --rewards sparse   --goal detailed --seed 18 --test --silent -f --output games/tw-rewardsSparse_goalDetailed.z8
tw-make tw-simple --rewards dense    --goal brief    --seed 18 --test --silent -f --output games/tw-rewardsDense_goalBrief.z8
tw-make tw-simple --rewards balanced --goal brief    --seed 18 --test --silent -f --output games/tw-rewardsBalanced_goalBrief.z8
tw-make tw-simple --rewards sparse   --goal brief    --seed 18 --test --silent -f --output games/tw-rewardsSparse_goalBrief.z8
tw-make tw-simple --rewards sparse   --goal none     --seed 18 --test --silent -f --output games/tw-rewardsSparse_goalNone.z8
