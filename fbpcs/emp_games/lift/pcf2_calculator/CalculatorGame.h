/*
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */

#pragma once

#include "fbpcf/engine/communication/IPartyCommunicationAgentFactory.h"
#include "fbpcf/frontend/mpcGame.h"
#include "fbpcs/emp_games/common/Constants.h"
#include "fbpcs/emp_games/lift/pcf2_calculator/Aggregator.h"
#include "fbpcs/emp_games/lift/pcf2_calculator/Attributor.h"
#include "fbpcs/emp_games/lift/pcf2_calculator/CalculatorGameConfig.h"
#include "fbpcs/emp_games/lift/pcf2_calculator/input_processing/DecoupledUDPInputProcessor.h"
#include "fbpcs/emp_games/lift/pcf2_calculator/input_processing/InputData.h"
#include "fbpcs/emp_games/lift/pcf2_calculator/input_processing/InputProcessor.h"
#include "fbpcs/emp_games/lift/pcf2_calculator/input_processing/SecretShareInputProcessor.h"

namespace private_lift {
template <int schedulerId>
class CalculatorGame : public fbpcf::frontend::MpcGame<schedulerId> {
 public:
  CalculatorGame(
      const int party,
      std::unique_ptr<fbpcf::scheduler::IScheduler> scheduler,
      std::shared_ptr<
          fbpcf::engine::communication::IPartyCommunicationAgentFactory>
          communicationAgentFactory)
      : fbpcf::frontend::MpcGame<schedulerId>(std::move(scheduler)),
        party_{party},
        communicationAgentFactory_(communicationAgentFactory) {}

  std::string play(const CalculatorGameConfig& config) {
    if (config.inputData.getNumRows() == 0) {
      XLOG(WARN) << "skipped calculating as numRows==0.";
      // skip game::run(), just output the default metrics.
      return GroupedLiftMetrics().toJson();
    }

    auto inputProcessor = InputProcessor<schedulerId>(
        party_, config.inputData, config.numConversionsPerUser);
    auto attributor = std::make_unique<Attributor<schedulerId>>(
        party_, std::make_unique<InputProcessor<schedulerId>>(inputProcessor));
    auto aggregator = Aggregator<schedulerId>(
        party_,
        std::make_unique<InputProcessor<schedulerId>>(
            std::move(inputProcessor)),
        std::move(attributor),
        config.numConversionsPerUser,
        communicationAgentFactory_);
    return aggregator.toJson();
  }

  std::string playFromSecretShares(
      const std::string& globalParamsInputPath,
      const std::string& inputExpandedKeyPath,
      const std::string& inputPath,
      bool useDecoupledUDP,
      size_t numConversionPerUser) {
    std::shared_ptr<IInputProcessor<schedulerId>> inputProcessor;
    if (useDecoupledUDP) {
      inputProcessor =
          std::make_shared<DecoupledUDPInputProcessor<schedulerId>>(
              party_,
              globalParamsInputPath,
              inputExpandedKeyPath,
              inputPath,
              numConversionPerUser);
    } else {
      inputProcessor = std::make_shared<SecretShareInputProcessor<schedulerId>>(
          globalParamsInputPath, inputPath);
    }
    XLOG(INFO) << "Have " << inputProcessor->getLiftGameProcessedData().numRows
               << " values in inputData.";
    if (inputProcessor->getLiftGameProcessedData().numRows == 0) {
      XLOG(WARN) << "skipped calculating as numRows==0.";
      // skip game::run(), just output the default metrics.
      return GroupedLiftMetrics(
                 inputProcessor->getLiftGameProcessedData().numPartnerCohorts,
                 inputProcessor->getLiftGameProcessedData()
                     .numPublisherBreakdowns)
          .toJson();
    }

    auto attributor =
        std::make_unique<Attributor<schedulerId>>(party_, inputProcessor);
    auto aggregator = Aggregator<schedulerId>(
        party_,
        inputProcessor,
        std::move(attributor),
        numConversionPerUser,
        communicationAgentFactory_);
    return aggregator.toJson();
  }

 private:
  const int party_;
  std::shared_ptr<fbpcf::engine::communication::IPartyCommunicationAgentFactory>
      communicationAgentFactory_;
};
} // namespace private_lift
