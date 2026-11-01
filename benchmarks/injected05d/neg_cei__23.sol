pragma solidity 0.5.12;

contract Wallet6479 {
    address public owner;
    uint256 public supply;
    mapping(address => uint256) public credit;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        credit[msg.sender] += msg.value;
        supply += msg.value;
    }
    function withdraw(uint256 amount) public {
        require(credit[msg.sender] >= amount);
        credit[msg.sender] -= amount;
        supply -= amount;
        (bool ok, ) = msg.sender.call.value(amount)("");
        require(ok);
    }
}
