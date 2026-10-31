pragma solidity 0.5.12;

contract Ledger6984 {
    address public owner;
    uint256 public reserve;
    mapping(address => uint256) public credit;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        credit[msg.sender] += msg.value;
        reserve += msg.value;
    }
    address[] public members;

    function join() public {
        members.push(msg.sender);
    }

    function creditAll() public {
        for (uint256 i = 0; i < members.length; i++) {
            members[i].balance;
        }
    }

    function totalDeposits() public view returns (uint256) { return reserve; }

    function setOwner(address next) public { require(msg.sender == owner); owner = next; }
}
