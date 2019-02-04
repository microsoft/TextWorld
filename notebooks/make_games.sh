tw-make tw-simple --rewards dense    --goal detailed --seed 18 --test --silent -f --output games/rewardsDense_goalDetailed.ulx
tw-make tw-simple --rewards balanced --goal detailed --seed 18 --test --silent -f --output games/rewardsBalanced_goalDetailed.ulx
tw-make tw-simple --rewards sparse   --goal detailed --seed 18 --test --silent -f --output games/rewardsSparse_goalDetailed.ulx
tw-make tw-simple --rewards dense    --goal brief    --seed 18 --test --silent -f --output games/rewardsDense_goalBrief.ulx
tw-make tw-simple --rewards balanced --goal brief    --seed 18 --test --silent -f --output games/rewardsBalanced_goalBrief.ulx
tw-make tw-simple --rewards sparse   --goal brief    --seed 18 --test --silent -f --output games/rewardsSparse_goalBrief.ulx
tw-make tw-simple --rewards sparse   --goal none     --seed 18 --test --silent -f --output games/rewardsSparse_goalNone.ulx
